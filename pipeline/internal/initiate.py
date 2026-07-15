import random
import numpy as np
from qiskit import QuantumCircuit, QuantumRegister

import customise


def DimensionGiver(n):
    N = n
    Possible_Pairs = []
    for i in range(2, N):
        if (N % i == 0):
            if (i <= (N / i)):
                Possible_Pairs.append([i, int(N / i)])
            else:
                Possible_Pairs.append([int(N / i), i])
    Dimension = random.choice(Possible_Pairs)
    return Dimension


def GiveHammingWeight(x):
    BitX = bin(x)[2:]
    return BitX.count("1")


def GiveParity(x):
    return GiveHammingWeight(x) % 2


def KeyChoice(dimension):
    x, y = dimension
    target_parity = GiveParity(x) ^ GiveParity(y)

    repeat = True
    while repeat:
        key_x = random.randrange(2, x + 1, 2)
        key_y = random.randint(1, y)
        if (GiveParity(key_x) ^ GiveParity(key_y)) == target_parity:
            repeat = False

    return [key_x, key_y]


def GiveQubitCount(dimension):
    x, y = dimension
    QubitCount = [int(np.ceil(np.log2(x + 1))), int(np.ceil(np.log2(y + 1)))]
    return QubitCount


def Initiate():
    N = random.choice(customise.N_VALUES)
    Dimension = DimensionGiver(N)
    print(f"Dimension: {Dimension}")
    print(f"Key : {KeyChoice(Dimension)}")

    register_A = QuantumRegister(GiveQubitCount(Dimension)[0], name='Width')
    register_B = QuantumRegister(GiveQubitCount(Dimension)[1], name='Height')
    ancilla = QuantumRegister(3, name='Ancilla')

    circuit = QuantumCircuit(register_A, register_B, ancilla)
    print(f"Given N: {N}")
    return circuit, N
