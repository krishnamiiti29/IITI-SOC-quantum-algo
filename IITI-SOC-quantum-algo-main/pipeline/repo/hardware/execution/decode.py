def decode_bitstring(bitstring, width_qubits, height_qubits):
    bits = bitstring[::-1]
    x_bits = bits[0:width_qubits]
    y_bits = bits[width_qubits:width_qubits + height_qubits]
    x_val = int(x_bits[::-1], 2)
    y_val = int(y_bits[::-1], 2)
    return x_val, y_val


def key_to_bitstring(key, width_qubits, height_qubits):
    x_bits = format(key[0], f"0{width_qubits}b")[::-1]
    y_bits = format(key[1], f"0{height_qubits}b")[::-1]
    full = (x_bits + y_bits)[::-1]
    return full
