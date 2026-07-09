"""
Phase 2: build the constrained even superposition over the search qubits.

Extracted from the notebook's "Defining the function which creates even
superposition" cell.
"""

import numpy as np


def CreateConstrainedEvenSuperposition(Space, N, width):
    """
    Apply Hadamards to every search qubit except qubit 0 (the LSB), so it
    stays |0>, forcing every x in the superposition to be even -- matching
    KeyChoice's even key_x constraint.
    """
    n = int(np.ceil(np.log2(N)))
    targets = [q for q in range(n) if q != 0]
    Space.h(targets)
    return Space
