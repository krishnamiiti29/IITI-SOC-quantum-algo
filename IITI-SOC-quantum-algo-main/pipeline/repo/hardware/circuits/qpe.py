import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.quantum_info import Operator
from qiskit.circuit.library import QFT, UnitaryGate


def build_qpe_circuit(U, n_work, N, gamma, init_state=1, t_phase=None, add_measurement=False):
    """
    Assemble the order-finding QPE circuit and return it, unrun.

    Parameters
    ----------
    U : np.ndarray, qiskit Operator, or Operator-convertible
        Unitary acting on n_work qubits; U|y> = |gamma * y mod N>.
    n_work : int
        Qubits in the work register (2**n_work >= N).
    N : int
        Modulus / value being factored.
    gamma : int
        Base element whose order mod N is sought.
    t_phase : int, optional
        Qubits in the phase register. Defaults to 2*n_work + 1.
    init_state : int, optional
        Computational basis state to load into the work register (default 1).
    add_measurement : bool, optional
        If True, appends measurement of the phase register to a classical
        register named "phase_meas".

    Returns
    -------
    qc : QuantumCircuit
        The assembled, unrun circuit.
    t_phase : int
        Number of phase qubits actually used.
    """
    if 2 ** n_work < N:
        raise ValueError(f"n_work={n_work} cannot represent values mod N={N}")
    if t_phase is None:
        t_phase = 2 * n_work + 1

    U_matrix = np.asarray(Operator(U).data)
    expected_dim = 2 ** n_work
    if U_matrix.shape != (expected_dim, expected_dim):
        raise ValueError(f"U has shape {U_matrix.shape}, expected ({expected_dim}, {expected_dim})")

    phase_reg = QuantumRegister(t_phase, "phase")
    work_reg = QuantumRegister(n_work, "work")
    qc = QuantumCircuit(phase_reg, work_reg)

    # initialize work register to |init_state>
    bits = format(init_state, f"0{n_work}b")[::-1]
    for i, b in enumerate(bits):
        if b == "1":
            qc.x(work_reg[i])
    qc.barrier(label="init")

    # Hadamard layer
    qc.h(phase_reg)
    qc.barrier(label="H layer")

    # controlled U^(2^k) layer
    for k in range(t_phase):
        power = 2 ** k
        mat_power = np.linalg.matrix_power(U_matrix, power)
        gate = UnitaryGate(mat_power, label=f"U^{power}").control(1)
        qc.append(gate, [phase_reg[k]] + list(work_reg))
    qc.barrier(label="controlled-U powers")

    # inverse QFT
    qc.append(QFT(num_qubits=t_phase, inverse=True, do_swaps=True).to_gate(label="IQFT"), phase_reg)
    qc.barrier(label="IQFT")

    if add_measurement:
        creg = ClassicalRegister(t_phase, "phase_meas")
        qc.add_register(creg)
        qc.measure(phase_reg, creg)

    return qc, t_phase
