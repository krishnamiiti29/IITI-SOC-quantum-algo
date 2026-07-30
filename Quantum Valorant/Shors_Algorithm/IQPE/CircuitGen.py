from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
import math
from qiskit.circuit.library import PhaseGate
from qiskit.circuit.library import UnitaryGate

from FilePipeline.Shors_Algorithm.BuildUnitary import *


def build_iqpe_circuit(U, precision):
    """
    Build an IQPE circuit for a unitary U.

    Parameters
    ----------
    U : QuantumCircuit
        The unitary whose eigenphase is being estimated.
    precision : int
        Number of phase bits to estimate.

    Returns
    -------
    circuit : QuantumCircuit
        IQPE circuit.
    """
    n = U.num_qubits

    phase_qubit = QuantumRegister(1, "phase")
    system = QuantumRegister(n, "system")
    phase_bits = ClassicalRegister(precision, "phase_bits")

    circuit = QuantumCircuit(phase_qubit, system, phase_bits)

    # NOTE: system must be initialized to an eigenstate of U (or a state
    # with overlap on one). |1> is used here as a placeholder starting state for Shor-style modular multiplication.
    circuit.x(system[0])

    for k in range(precision - 1, -1, -1):
        circuit.reset(phase_qubit[0])
        circuit.h(phase_qubit[0])

        # Controlled U^(2^k)
        exponent = 2 ** k
        U_power = power_of_unitary(U, exponent)
        matrix_data = U_power.data if hasattr(U_power, 'data') else U_power

        gate_instruction = UnitaryGate(matrix_data, check_input=False)
        controlled_U_power = gate_instruction.control(num_ctrl_qubits=1)

        circuit.append(controlled_U_power, [phase_qubit[0]] + list(system))

        # Phase feedback: classical conditional correction based on
        # previously measured bits. angle = -2π * 0.b_(k+1)...b_(m-1)
        if k < precision - 1:
            for j in range(k + 1, precision):
                angle = -math.pi / (2 ** (j - k))
                with circuit.if_test((phase_bits[j], 1)):
                    circuit.p(angle, phase_qubit[0])

        circuit.h(phase_qubit[0])
        circuit.measure(phase_qubit[0], phase_bits[k])

    return circuit