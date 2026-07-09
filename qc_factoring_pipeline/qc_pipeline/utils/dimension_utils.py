"""
Internal utility functions for turning an integer N into a 2D search-space
dimension, computing Hamming weight / parity, choosing a target key that is
consistent with that parity, and sizing the qubit registers needed to
represent the dimension.

Extracted from the notebook's "Internal Function Definitions" cell.
"""

import random

import numpy as np


def DimensionGiver(n):
    """Return a random [width, height] factor pair of n, with width <= height."""
    N = n
    Possible_Pairs = []
    for i in range(2, N):
        if N % i == 0:
            if i <= (N / i):
                Possible_Pairs.append([i, int(N / i)])
            else:
                # Keep width as the smaller value, height as the larger value,
                # so downstream code can consistently rely on that ordering.
                Possible_Pairs.append([int(N / i), i])
    Dimension = random.choice(Possible_Pairs)
    return Dimension


def GiveHammingWeight(x):
    """Return the number of 1-bits in the binary representation of x."""
    BitX = bin(x)[2:]
    return BitX.count("1")


def GiveParity(x):
    """Return the parity (0 or 1) of the Hamming weight of x."""
    return GiveHammingWeight(x) % 2


def KeyChoice(dimension):
    """
    Choose a random key [key_x, key_y] within the given (x, y) dimension such
    that key_x is even (even superposition requirement) and the combined
    parity of key_x/key_y matches the target parity derived from the
    dimension itself.
    """
    x, y = dimension
    target_parity = GiveParity(x) ^ GiveParity(y)

    repeat = True
    while repeat:
        # Even key_x, per the even-superposition requirement.
        key_x = random.randrange(2, x + 1, 2)
        key_y = random.randint(1, y)
        if (GiveParity(key_x) ^ GiveParity(key_y)) == target_parity:
            repeat = False

    return [key_x, key_y]


def GiveQubitCount(dimension):
    """Return the [width_qubits, height_qubits] needed to represent dimension."""
    x, y = dimension
    QubitCount = [int(np.ceil(np.log2(x))), int(np.ceil(np.log2(y)))]
    return QubitCount
