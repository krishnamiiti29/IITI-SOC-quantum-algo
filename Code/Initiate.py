import numpy as np
import random
import qiskit as qc
from qiskit import QuantumCircuit, QuantumRegister

def DimensionGiver(n):
  N = n
  Possible_Pairs = []
  for i in range(2,N):
    if (N % i == 0):
      if (i <= (N / i)):
        Possible_Pairs.append([i, int(N / i)])
      else:     #This Stuff is so that we define width as the smaller value, and height as larger value to consistantly be able to compute
        Possible_Pairs.append([int(N / i), i])
  Dimension = random.choice(Possible_Pairs)
  return Dimension

def KeyChoice(dimension):
  x, y = dimension
  key_x = random.randrange(2, x+1, 2)
  key_y = random.randint(1, y)
  return [key_x, key_y]

def GiveQubitCount(dimension):
  x, y = dimension
  QubitCount = [int(np.ceil(np.log2(x))),int(np.ceil(np.log2(y)))]
  return QubitCount

def Initiate():
  NumberChoices = [27]
  N = random.choice(NumberChoices)
  Dimension = DimensionGiver(N)
  print(f"Dimension: {Dimension}")
  print(f"Key : {KeyChoice(Dimension)}")
  register_A = QuantumRegister(GiveQubitCount(Dimension)[0], name='Width')
  register_B = QuantumRegister(GiveQubitCount(Dimension)[1], name='Height')
  circuit = QuantumCircuit(register_A, register_B)
  print(f"Given N: {N}")
  return circuit, N