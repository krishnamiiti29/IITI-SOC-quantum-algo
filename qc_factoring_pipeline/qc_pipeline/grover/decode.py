"""
Decode measured bitstrings back into (x, y) search-space coordinates, and
the inverse: encode a target key into its expected bitstring.

Extracted from the notebook's simulator/hardware measurement-decoding cells.
"""


def decode_bitstring(bitstring, width_qubits, height_qubits):
    """
    Decode a measured bitstring into (x, y).

    Qiskit reports bitstrings with qubit (n-1) leftmost and qubit 0
    rightmost, so we reverse before slicing out the x-register and
    y-register bits.
    """
    bits = bitstring[::-1]
    x_bits = bits[0:width_qubits]
    y_bits = bits[width_qubits:width_qubits + height_qubits]
    x_val = int(x_bits[::-1], 2)
    y_val = int(y_bits[::-1], 2)
    return x_val, y_val


def key_to_bitstring(key, width_qubits, height_qubits):
    """Encode a target [x, y] key into the bitstring Qiskit would report for it."""
    x_bits = format(key[0], f"0{width_qubits}b")[::-1]
    y_bits = format(key[1], f"0{height_qubits}b")[::-1]
    full = (x_bits + y_bits)[::-1]
    return full


def decode_counts(counts, width_qubits, height_qubits):
    """Aggregate a Qiskit counts dict into counts keyed by decoded (x, y) tuples."""
    decoded = {}
    for bitstring, count in counts.items():
        xy = decode_bitstring(bitstring, width_qubits, height_qubits)
        decoded[xy] = decoded.get(xy, 0) + count
    return decoded
