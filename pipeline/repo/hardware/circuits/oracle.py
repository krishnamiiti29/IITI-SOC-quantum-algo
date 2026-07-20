import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import MCPhaseGate

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


def ApplyHammingWeightResonanceOracle(Space, width, n, target_parity, angle=PI3_ANGLE):
    """
    Fixed-point GROVER ORACLE.

    Computes anc_px = HW(x) XOR HW(y) (mod 2) into an ancilla, then -- rather
    than a full bit flip / pi phase kickback -- applies the fixed pi/3 phase
    rotation to exactly the branches where anc_px == target_parity. This is
    the "marking" half of the matched oracle/diffuser pair used by
    fixed-point Grover.
    """
    anc_px, anc_py = n, n + 1
    x_qubits = list(range(0, width))
    y_qubits = list(range(width, n))

    for q in x_qubits:
        Space.cx(q, anc_px)
    for q in y_qubits:
        Space.cx(q, anc_py)

    Space.cx(anc_py, anc_px)  # anc_px now holds HW(x) XOR HW(y) mod 2

    if target_parity == 0:
        Space.x(anc_px)

    # Apply the pi/3 phase (not a bit flip) to marked branches only.
    Space.p(angle, anc_px)

    if target_parity == 0:
        Space.x(anc_px)

    # Uncompute ancillas.
    Space.cx(anc_py, anc_px)
    for q in reversed(y_qubits):
        Space.cx(q, anc_py)
    for q in reversed(x_qubits):
        Space.cx(q, anc_px)

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
