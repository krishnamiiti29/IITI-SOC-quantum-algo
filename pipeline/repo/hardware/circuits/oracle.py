import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import MCPhaseGate

from hardware.circuits.popcount import build_popcount_circuit, count_register_size

# Fixed, non-pi phase used by L.K. Grover's (2005) "fixed-point" search.
# Using this same partial-reflection angle in BOTH the oracle and the
# diffuser (instead of the usual pi phase flip) makes amplitude grow
# monotonically toward the marked subspace -- it never overshoots the
# target, so the algorithm stays robust even when the number of
# iterations needed isn't known in advance.
PI3_ANGLE = np.pi / 3


def CreateConstrainedEvenSuperposition(Space, width_qubits, height_qubits):
    """
    Prepares the search register's superposition to match KeyChoice's
    classical constraint: x (the width register) is restricted to strictly
    EVEN Hamming weight, while y (the height register) is left fully free.

    Construction on the x register: Hadamard every x qubit except the last,
    then force the last x qubit to equal the XOR (parity) of the others.
    That guarantees every x value left with nonzero amplitude has even
    Hamming weight. A single-qubit x register has no nonzero even-weight
    value besides |0>, so it's simply left unprepared (stays |0>).
    """
    x_qubits = list(range(width_qubits))
    y_qubits = list(range(width_qubits, width_qubits + height_qubits))

    # y register: fully free superposition, no constraint.
    Space.h(y_qubits)

    # x register: constrained so HW(x) is always even.
    if width_qubits >= 2:
        free_x_qubits = x_qubits[:-1]
        parity_x_qubit = x_qubits[-1]
        Space.h(free_x_qubits)
        for q in free_x_qubits:
            Space.cx(q, parity_x_qubit)
    # width_qubits == 1 (or 0): only x=0 has even weight, leave as |0>.

    return Space


def ApplyHammingWeightResonanceOracle(
        Space,
        width,
        n,
        target_weight,
        angle=PI3_ANGLE):

    x_qubits = list(range(width))
    y_qubits = list(range(width, n))

    # Iterate through every computational basis state.
    for x in range(2 ** len(x_qubits)):
        hw_x = bin(x).count("1")

        for y in range(2 ** len(y_qubits)):
            hw_y = bin(y).count("1")

            # Oracle condition
            if (hw_x ^ hw_y) != target_weight:
                continue

            # Select |x,y>
            for i, q in enumerate(x_qubits):
                if ((x >> i) & 1) == 0:
                    Space.x(q)

            for i, q in enumerate(y_qubits):
                if ((y >> i) & 1) == 0:
                    Space.x(q)

            # π/3 phase oracle
            controls = x_qubits + y_qubits

            if len(controls) == 1:
                Space.p(angle, controls[0])
            else:
                gate = MCPhaseGate(angle,
                                   num_ctrl_qubits=len(controls)-1)

                Space.append(gate, controls)

            # Undo state selection
            for i, q in enumerate(y_qubits):
                if ((y >> i) & 1) == 0:
                    Space.x(q)

            for i, q in enumerate(x_qubits):
                if ((x >> i) & 1) == 0:
                    Space.x(q)

    return Space


def build_pi3_diffuser(num_search_qubits, angle=PI3_ANGLE):
    """
    Fixed-point GROVER DIFFUSION operator.

    Standard inversion-about-the-mean, but the reflection phase is the same
    pi/3 used by the oracle (instead of the usual pi phase flip), so oracle
    and diffuser apply matched partial reflections each round.
    """
    qc = QuantumCircuit(num_search_qubits, name='D_pi/3')

    qc.h(range(num_search_qubits))
    qc.x(range(num_search_qubits))

    mcp = MCPhaseGate(angle, num_ctrl_qubits=num_search_qubits - 1)
    qc.append(mcp, list(range(num_search_qubits)))

    qc.x(range(num_search_qubits))
    qc.h(range(num_search_qubits))

    return qc.to_instruction()


def build_fixed_point_grover_circuit(Space, width_qubits, height_qubits, target_parity,
                                      iterations, angle=PI3_ANGLE):
    """
    Assembles Grover's (2005) fixed-point search circuit: `iterations`
    repetitions of the matched pi/3 oracle + pi/3 diffuser pair, applied to
    the constrained-even-superposition search register. Because both
    reflections share the same non-pi angle, amplitude on the target
    subspace increases monotonically without overshoot, so `iterations`
    can safely be chosen generously even without knowing the true solution
    count in advance.
    """
    n = width_qubits + height_qubits
    diffuser = build_pi3_diffuser(n, angle)

    for _ in range(iterations):
        Space = ApplyHammingWeightResonanceOracle(Space, width_qubits, n, target_parity, angle)
        Space.append(diffuser, list(range(n)))

    return Space


# ---------------------------------------------------------------------------
# New, additive popcount-based oracle. Does NOT modify or replace anything
# above. Implements:
#
#     |x>, |y> -> Popcount -> |HW(x)>, |HW(y)> -> XOR -> |HW(x) XOR HW(y)>
#              -> Compare with HW(w||h) -> pi/3 Phase Oracle
#              -> Uncompute XOR -> Uncompute HW(x), HW(y)
#
# using real quantum sub-circuits (hardware/circuits/popcount.py) instead of
# the classical enumerate-and-flag approach used by
# ApplyHammingWeightResonanceOracle above.
# ---------------------------------------------------------------------------

def build_popcount_subcircuits(width_qubits, height_qubits):
    """
    Builds the (popcount_x_circ, popcount_y_circ, m) triple used by
    ApplyHammingWeightPopcountOracle. Factored out so callers that invoke
    the oracle repeatedly (e.g. once per Grover iteration) can build these
    once and pass them in via `popcount_circs=`, instead of re-synthesizing
    the same gates on every call.
    """
    m = max(count_register_size(width_qubits), count_register_size(height_qubits))
    popcount_x_circ = build_popcount_circuit(width_qubits, m, name="popcount_x")
    popcount_y_circ = build_popcount_circuit(height_qubits, m, name="popcount_y")
    return popcount_x_circ, popcount_y_circ, m


def ApplyHammingWeightPopcountOracle(Space, width_qubits, height_qubits, target_weight,
                                      angle=PI3_ANGLE, popcount_circs=None):
    """
    Quantum-circuit oracle: computes HW(x) and HW(y) into ancilla "count"
    registers via build_popcount_circuit, XORs them together, applies the
    pi/3 phase when the XOR matches target_weight, then fully uncomputes
    the XOR and both popcount ancillas so the ancilla qubits are returned
    to |0> and can be reused across Grover iterations.

    Requires `Space` to already contain, beyond the width_qubits + height_
    qubits search register, at least 2 * m extra ancilla qubits, where
    m = max(count_register_size(width_qubits), count_register_size(height_qubits)).

    `popcount_circs`, if given, should be the (popcount_x_circ, popcount_y_circ,
    m) tuple returned by build_popcount_subcircuits -- this lets a caller
    that invokes this function many times (e.g. once per Grover iteration)
    build the popcount sub-circuits once and reuse them, instead of paying
    the gate-synthesis cost on every call.
    """
    x_qubits = list(range(width_qubits))
    y_qubits = list(range(width_qubits, width_qubits + height_qubits))
    n_search = width_qubits + height_qubits

    if popcount_circs is None:
        popcount_circs = build_popcount_subcircuits(width_qubits, height_qubits)
    popcount_x_circ, popcount_y_circ, m = popcount_circs

    count_x_qubits = list(range(n_search, n_search + m))
    count_y_qubits = list(range(n_search + m, n_search + 2 * m))

    if Space.num_qubits < n_search + 2 * m:
        raise ValueError(
            f"Space needs at least {n_search + 2 * m} qubits for the popcount "
            f"oracle (search register={n_search}, two count registers of size "
            f"{m} each); got {Space.num_qubits}."
        )

    # Compute HW(x) -> count_x, HW(y) -> count_y
    Space.append(popcount_x_circ.to_instruction(), x_qubits + count_x_qubits)
    Space.append(popcount_y_circ.to_instruction(), y_qubits + count_y_qubits)

    # XOR: count_x <- HW(x) XOR HW(y)
    for cx_q, cy_q in zip(count_x_qubits, count_y_qubits):
        Space.cx(cy_q, cx_q)

    # Compare count_x (now HW(x) XOR HW(y)) against target_weight: flip the
    # bits of count_x where target_weight has a 0, so "all ones" on
    # count_x_qubits means "match", then apply the shared pi/3 phase.
    target_bits = format(target_weight, f"0{m}b")[::-1]  # LSB-first, matches count_x_qubits order
    flipped = []
    for i, b in enumerate(target_bits):
        if b == "0":
            Space.x(count_x_qubits[i])
            flipped.append(count_x_qubits[i])

    if m == 1:
        Space.p(angle, count_x_qubits[0])
    else:
        gate = MCPhaseGate(angle, num_ctrl_qubits=m - 1)
        Space.append(gate, count_x_qubits)

    for q in flipped:
        Space.x(q)

    # Uncompute XOR
    for cx_q, cy_q in zip(count_x_qubits, count_y_qubits):
        Space.cx(cy_q, cx_q)

    # Uncompute popcounts (restores count_x, count_y ancillas to |0>)
    Space.append(popcount_y_circ.inverse().to_instruction(label="popcount_y_dg"), y_qubits + count_y_qubits)
    Space.append(popcount_x_circ.inverse().to_instruction(label="popcount_x_dg"), x_qubits + count_x_qubits)

    return Space


def build_fixed_point_grover_circuit_popcount(Space, width_qubits, height_qubits, target_parity,
                                               iterations, angle=PI3_ANGLE):
    """
    New, additive variant of build_fixed_point_grover_circuit that uses the
    popcount-based oracle (ApplyHammingWeightPopcountOracle) instead of the
    classical-enumeration oracle. The fixed-point pi/3 diffuser is unchanged
    and still acts only on the search register qubits [0, n).
    """
    n = width_qubits + height_qubits
    diffuser = build_pi3_diffuser(n, angle)
    popcount_circs = build_popcount_subcircuits(width_qubits, height_qubits)

    for _ in range(iterations):
        Space = ApplyHammingWeightPopcountOracle(Space, width_qubits, height_qubits, target_parity, angle,
                                                  popcount_circs=popcount_circs)
        Space.append(diffuser, list(range(n)))

    return Space
