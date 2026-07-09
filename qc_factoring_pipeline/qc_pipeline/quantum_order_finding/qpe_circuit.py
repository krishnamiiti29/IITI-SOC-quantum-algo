"""
Real QPE-based order finding circuit construction -- replaces the
classical-statevector RunIter approach with an actual quantum phase
estimation circuit.

Extracted from the notebook's "Real QPE-based order finding" cell.
"""

from fractions import Fraction

import numpy as np
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit.library import QFT
from qiskit.quantum_info import Operator


def BuildControlledPowerGate(Gamma, power, N):
    """
    Permutation matrix for x -> (Gamma^power * x) mod N, embedded on n
    qubits, then wrapped as a single-control gate for use inside QPE.
    """
    n = int(np.ceil(np.log2(N)))
    M = 2 ** n
    Gm = pow(int(Gamma), power, int(N))
    Umat = np.zeros((M, M))
    for y in range(M):
        output = (Gm * y) % N if y < N else y
        Umat[output][y] = 1
    gate = Operator(Umat).to_instruction()
    gate.name = f"U^{power}"
    return gate.control(1)


def BuildQPEOrderFindingCircuit(Gamma, N, t=None):
    """Build a full QPE circuit for order finding of Gamma mod N."""
    n = int(np.ceil(np.log2(N)))
    if t is None:
        t = 2 * n + 3  # extra precision qubits for reliable continued-fraction recovery

    counting = QuantumRegister(t, name="count")
    work = QuantumRegister(n, name="work")
    creg = ClassicalRegister(t, name="c")
    qpe = QuantumCircuit(counting, work, creg)

    qpe.x(work[0])   # start work register in |1>
    qpe.h(counting)  # counting register into superposition

    for k in range(t):
        cU = BuildControlledPowerGate(Gamma, 2 ** k, N)
        qpe.append(cU, [counting[k]] + list(work))

    qpe.append(QFT(t, inverse=True), counting)
    qpe.measure(counting, creg)
    return qpe, t


def PhaseToOrder(measured_int, t, N):
    """Convert a measured QPE integer into an order candidate via continued fractions."""
    phase = measured_int / (2 ** t)
    frac = Fraction(phase).limit_denominator(N)
    return frac.denominator
