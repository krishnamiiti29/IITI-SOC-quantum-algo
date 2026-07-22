
import numpy as np
from qiskit import QuantumCircuit


def count_register_size(num_input_qubits):

    if num_input_qubits <= 0:
        return 1
    return int(np.ceil(np.log2(num_input_qubits + 1))) or 1


def controlled_increment(qc, control, count_qubits):

    m = len(count_qubits)
    for i in reversed(range(1, m)):
        qc.mcx([control] + list(count_qubits[:i]), count_qubits[i])
    qc.cx(control, count_qubits[0])


def build_popcount_circuit(num_input_qubits, count_qubits_size=None, name="popcount"):

    if count_qubits_size is None:
        count_qubits_size = count_register_size(num_input_qubits)

    qc = QuantumCircuit(num_input_qubits + count_qubits_size, name=name)
    input_qubits = list(range(num_input_qubits))
    count_qubits = list(range(num_input_qubits, num_input_qubits + count_qubits_size))

    for q in input_qubits:
        controlled_increment(qc, q, count_qubits)

    return qc
