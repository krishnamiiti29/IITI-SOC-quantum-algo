import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import MCPhaseGate as MCPGate


def CreateConstrainedEvenSuperposition(Space, N, width):
    n = int(np.ceil(np.log2(N)))
    targets = list(range(n))
    Space.h(targets)
    return Space


def ApplyHammingWeightResonanceOracle(Space, width, n, target_parity):
    anc_px, anc_py, target = n, n + 1, n + 2
    x_qubits = list(range(0, width))
    y_qubits = list(range(width, n))

    for q in x_qubits:
        Space.cx(q, anc_px)
    for q in y_qubits:
        Space.cx(q, anc_py)

    Space.cx(anc_py, anc_px)

    if target_parity == 1:
        Space.x(anc_px)

    Space.cx(anc_px, target)

    if target_parity == 1:
        Space.x(anc_px)
    Space.cx(anc_py, anc_px)
    for q in reversed(y_qubits):
        Space.cx(q, anc_py)
    for q in reversed(x_qubits):
        Space.cx(q, anc_px)

    return Space


def build_pi3_diffuser(num_search_qubits):
    qc = QuantumCircuit(num_search_qubits, name='D_pi/3')

    qc.h(range(num_search_qubits))
    qc.x(range(num_search_qubits))

    mcp = MCPGate(np.pi / 3, num_ctrl_qubits=num_search_qubits - 1)
    qc.append(mcp, list(range(num_search_qubits)))

    qc.x(range(num_search_qubits))
    qc.h(range(num_search_qubits))

    return qc.to_instruction()
