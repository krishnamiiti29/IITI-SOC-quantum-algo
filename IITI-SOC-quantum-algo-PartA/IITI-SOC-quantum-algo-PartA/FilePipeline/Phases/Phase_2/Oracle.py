"""
FilePipeline/Phases/Phase_2/Oracle.py

Hamming Weight resonance oracle for the fixed-point pi/3 Grover search.

Marks every (x, y) state in the search register satisfying:
    HW(x) XOR HW(y) == target_parity

where x is restricted to EVEN VALUES (LSB == 0), matching the constraint
imposed by EvenSuperposition.py and GenerateKey.py.

Nothing in Phase 1, Runner.py, EvenSuperposition.py, GenerateKey.py or
any other existing file is modified.
"""

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import MCPhaseGate

# Fixed pi/3 phase -- Grover (2005) fixed-point variant.
# Oracle and diffuser share this angle so amplitude on the marked subspace
# grows monotonically without overshoot across all iterations.
PI3_ANGLE = np.pi / 3


def GiveHammingWeight(x):
    return bin(x).count("1")


def ApplyHammingWeightOracle(QC, width, height, target_parity, angle=PI3_ANGLE):
    """
    Applies the pi/3 Hamming Weight resonance phase oracle to QC in-place.

    Marks every basis state |x, y> where:
        (HW(x) XOR HW(y)) % 2 == target_parity
    and x is an even value (LSB == 0), consistent with EvenSuperposition.py.

    Parameters
    ----------
    QC           : QuantumCircuit  -- the search register circuit
    width        : int             -- number of width qubits
    height       : int             -- number of height qubits
    target_parity: int (0 or 1)   -- parity to mark
    angle        : float           -- phase angle (default pi/3)
    """
    n = width + height
    x_qubits = list(range(width))
    y_qubits = list(range(width, n))

    for x in range(0, 2 ** width, 2):          # even x values only (LSB=0)
        hw_x = GiveHammingWeight(x)

        for y in range(2 ** height):
            hw_y = GiveHammingWeight(y)

            if (hw_x ^ hw_y) % 2 != target_parity:
                continue

            # Select |x, y> -- flip qubits that should be 0 for this state
            flipped = []
            for i, q in enumerate(x_qubits):
                if ((x >> i) & 1) == 0:
                    QC.x(q)
                    flipped.append(q)
            for i, q in enumerate(y_qubits):
                if ((y >> i) & 1) == 0:
                    QC.x(q)
                    flipped.append(q)

            # Apply pi/3 phase conditioned on all qubits being |1>
            controls = x_qubits + y_qubits
            if len(controls) == 1:
                QC.p(angle, controls[0])
            else:
                QC.append(MCPhaseGate(angle, num_ctrl_qubits=len(controls) - 1), controls)

            # Undo selection
            for q in flipped:
                QC.x(q)

    return QC


def BuildDiffuser(num_qubits, angle=PI3_ANGLE):
    """
    Fixed-point pi/3 Grover diffuser (inversion about the mean).
    Uses the same pi/3 angle as the oracle for matched partial reflections.
    """
    qc = QuantumCircuit(num_qubits, name="Diffuser_pi3")
    qc.h(range(num_qubits))
    qc.x(range(num_qubits))
    qc.append(MCPhaseGate(angle, num_ctrl_qubits=num_qubits - 1), list(range(num_qubits)))
    qc.x(range(num_qubits))
    qc.h(range(num_qubits))
    return qc.to_instruction()


def BuildGroverCircuit(QC, width, height, target_parity, iterations=8, angle=PI3_ANGLE):
    """
    Applies `iterations` rounds of (oracle + diffuser) to QC.
    The diffuser acts only on the search register qubits [0, width+height).
    """
    n = width + height
    diffuser = BuildDiffuser(n, angle)

    for _ in range(iterations):
        QC = ApplyHammingWeightOracle(QC, width, height, target_parity, angle)
        QC.append(diffuser, list(range(n)))

    return QC
