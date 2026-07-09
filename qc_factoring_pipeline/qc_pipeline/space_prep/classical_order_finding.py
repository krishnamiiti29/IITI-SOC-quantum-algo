"""
Classical (statevector-simulation based) order finding used to recover a
nontrivial factor pair of N via the period of x -> Gamma*x mod N.

Extracted from the notebook's "Automated Space Preparation" cell
(BuildUnitary / RunIter / ProvideDimensions).
"""

import math
import random

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Statevector


def BuildUnitary(Gamma, N):
    """Build the permutation unitary for x -> (Gamma * x) mod N on ceil(log2(N)) qubits."""
    n = int(np.ceil(np.log2(N)))
    M = 2 ** n

    U = np.zeros((M, M))

    for y in range(M):
        if y < N:
            output = (Gamma * y) % N
        else:
            output = y
        U[output][y] = 1
    return Operator(U)


def RunIter(n, U, N, Y):
    """
    Repeatedly apply unitary U to a basis state |Y> until the state returns
    to (the same argmax as) Y, i.e. until the order/period is found.
    """
    Y_int = int(Y, 2)
    print(f"Y = {Y_int}")

    qc = QuantumCircuit(n)
    for i in range(len(Y)):
        if Y[i] == "1":
            qc.x(len(Y) - 1 - i)

    for i in range(N):
        qc.unitary(U, range(n))
        Y_new = Statevector.from_instruction(qc)
        if (np.argmax(np.abs(Y_new.data)) == Y_int) & (i > 1):
            return i + 1


def ProvideDimensions(N):
    """
    Master call: given a total dimension N, use classical order finding
    (via statevector simulation) to recover a nontrivial factor pair of N,
    or return None if this attempt fails.
    """
    n = int(np.ceil(np.log2(N)))

    valid_Gamma = []
    for i in range(2, N):
        if math.gcd(i, N) == 1:
            valid_Gamma.append(i)

    Gamma = random.choice(valid_Gamma)
    U = BuildUnitary(Gamma, N)

    Y_val = random.randint(1, N)
    Y = format(Y_val, "b")

    r = RunIter(n, U, N, Y)
    if r is None:
        return None

    x = pow(int(Gamma), r // 2, int(N))
    if x == 1:
        return None

    Final1 = math.gcd(N, int(x + 1))
    Final2 = math.gcd(N, int(x - 1))
    for f in (Final1, Final2):
        if f > 1 and N % f == 0:
            other = N // f
            if other > 1:
                return (f, other)

    return None
