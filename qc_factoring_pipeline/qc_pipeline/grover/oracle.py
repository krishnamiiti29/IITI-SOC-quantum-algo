"""
Phase 3: the Hamming-weight resonance oracle and the pi/3 diffuser used to
amplify the target key state.

Extracted from the notebook's Grover oracle / diffuser cell.

Notes carried over from the original notebook:
  - Remember to change how key is chosen to fit HW(x) XOR HW(y) = HW(W|H)
  - Remember to check only the parity
  - Remember to use minimum ancilla
  - The purpose of phase 2 is only to reduce states by a factor of 2;
    phase 3 finds the keystate.
"""

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import MCPhaseGate as MCPGate


def ApplyHammingWeightResonanceOracle(Space, width, n, target_parity):
    """
    Flip an ancilla `target` qubit when HW(x) XOR HW(y) matches
    target_parity, using two scratch ancillas (anc_px, anc_py) that are
    uncomputed at the end.
    """
    anc_px, anc_py, target = n, n + 1, n + 2
    x_qubits = list(range(0, width))
    y_qubits = list(range(width, n))

    for q in x_qubits:
        Space.cx(q, anc_px)
    for q in y_qubits:
        Space.cx(q, anc_py)

    # combine both parities into anc_px: anc_px now = HW(x) + HW(y)
    Space.cx(anc_py, anc_px)

    # if target==1, flip anc_px once so "1" always means "condition holds"
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
    """Build a pi/3-phase Grover-style diffuser over the search qubits."""
    qc = QuantumCircuit(num_search_qubits, name="D_pi/3")

    qc.h(range(num_search_qubits))
    qc.x(range(num_search_qubits))

    mcp = MCPGate(np.pi / 3, num_ctrl_qubits=num_search_qubits - 1)
    qc.append(mcp, list(range(num_search_qubits)))

    qc.x(range(num_search_qubits))
    qc.h(range(num_search_qubits))

    return qc.to_instruction()
