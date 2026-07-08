import numpy as np
from qiskit.quantum_info import Operator, Statevector
from qiskit import QuantumCircuit

#Here, build unitary matrix
def BuildUnitary(Gamma, N):
  n = int(np.ceil(np.log2(N)))
  M = 2**n

  U = np.zeros((M, M))

  for y in range(M):
    if (y < N):
      output = (Gamma * y) % N
    else:
      output = y
    U[output][y] = 1
  return Operator(U)
