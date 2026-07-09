"""
Automated space preparation: pick a composite N, derive a factor-pair
dimension for it, and allocate the quantum registers/circuit that will hold
the search space.

Extracted from the notebook's "Automated Space Preparation" cell.
"""

import random

from qiskit import QuantumCircuit, QuantumRegister

from qc_pipeline.config import NUMBER_CHOICES, DEFAULT_ANCILLA_QUBITS
from qc_pipeline.utils.dimension_utils import (
    DimensionGiver,
    GiveQubitCount,
    KeyChoice,
)


def Initiate():
    """
    Pick a random N from NUMBER_CHOICES, derive a factor-pair dimension for
    it, and build a QuantumCircuit with Width/Height/Ancilla registers sized
    to that dimension.

    Returns:
        (circuit, N)
    """
    N = random.choice(NUMBER_CHOICES)
    Dimension = DimensionGiver(N)
    print(f"Dimension: {Dimension}")
    print(f"Key : {KeyChoice(Dimension)}")

    register_A = QuantumRegister(GiveQubitCount(Dimension)[0], name="Width")
    register_B = QuantumRegister(GiveQubitCount(Dimension)[1], name="Height")
    ancilla = QuantumRegister(DEFAULT_ANCILLA_QUBITS, name="Ancilla")

    circuit = QuantumCircuit(register_A, register_B, ancilla)

    print(f"Given N: {N}")
    return circuit, N
