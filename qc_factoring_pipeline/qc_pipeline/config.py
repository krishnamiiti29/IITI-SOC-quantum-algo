"""
Global configuration / constants for the quantum factoring pipeline.
"""

# Candidate N values used by space_prep.initiate.Initiate().
# Each is a semiprime-ish composite with a nontrivial factor pair, kept
# small enough that qubit counts stay tractable on simulators/NISQ hardware.
NUMBER_CHOICES = [
    4, 6, 9, 10, 14, 15, 21, 22, 25, 26, 33, 34, 35, 38, 39, 46, 49, 51, 55,
    57, 58, 62, 65, 69, 74, 77, 82, 85, 86, 87, 91, 93, 94, 95, 106, 111,
    115, 118, 119, 121, 122, 123, 129, 133, 134, 141, 142, 143, 145, 146,
    155, 158, 159, 161, 166, 169, 177, 178, 183, 185, 187, 194, 201, 202,
    203, 205, 206, 209, 213, 214, 215, 217, 218, 219, 221, 226, 235, 237,
    247, 249, 253, 254,
]

# Default number of ancilla qubits reserved by space_prep.initiate.Initiate().
DEFAULT_ANCILLA_QUBITS = 3
