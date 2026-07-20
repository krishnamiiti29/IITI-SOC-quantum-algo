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
    return GiveHammingWeight(x)


def KeyChoice(dimension):
    # Rule: HW(w|h) -- the Hamming weight of w and h concatenated -- is
    # mathematically equal to HW(w) + HW(h), since concatenation just
    # concatenates the bits and popcount is additive over concatenation.
    w, h = dimension
    target_weight = bin(w).count('1') + bin(h).count('1')

    # Find the (x, y) pair satisfying HW(x) XOR HW(y) == HW(w|h), with x
    # restricted to strictly EVEN Hamming weight. This constraint is what
    # CreateConstrainedEvenSuperposition (oracle.py) mirrors quantum-
    # mechanically when preparing the search register.
    for x in range(w + 1):
        hw_x = bin(x).count('1')
        if hw_x % 2 != 0:
            continue

        for y in range(h + 1):
            hw_y = bin(y).count('1')

            # Rule: Test if the XOR of their weights matches the target
            if (hw_x ^ hw_y) == target_weight:
                return [x, y]

    return {"status": "Failed", "message": "No valid key-state exists for these constraints"}


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
