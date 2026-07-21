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

    phase_bits : ClassicalRegister
        Classical register containing the phase bits.
    """

    n = U.num_qubits

    # --------------------------------------------------------
    # Registers
    # --------------------------------------------------------

    phase_qubit = QuantumRegister(1, "phase")

    system = QuantumRegister(n, "system")

    phase_bits = ClassicalRegister(precision, "phase_bits")

    circuit = QuantumCircuit(
        phase_qubit,
        system,
        phase_bits
    )

    # --------------------------------------------------------
    # Prepare the system state
    # --------------------------------------------------------

    circuit.x(system[0])

    # IMPORTANT:
    #
    # The system must be initialized to an eigenstate of U,
    # or to a state having overlap with an eigenstate.
    #
    # Here we use |0...0> as a generic placeholder.
    #
    # For Shor-style modular multiplication, this should
    # normally be replaced by the appropriate starting state,
    # such as |1>, depending on the construction of U.

    # Example:
    #
    # circuit.x(system[0])
    #
    # if |1> is desired.

    # --------------------------------------------------------
    # IQPE iterations
    # --------------------------------------------------------

    for k in range(precision - 1, -1, -1):

        # Reset phase qubit to |0>
        circuit.reset(phase_qubit[0])

        # Prepare |+>
        circuit.h(phase_qubit[0])

        # ----------------------------------------------------
        # Controlled U^(2^k)
        # ----------------------------------------------------

        exponent = 2 ** k

        U_power = power_of_unitary(U, exponent)

        matrix_data = U_power.data if hasattr(U_power, 'data') else U_power
        
        # Build the gate explicitly while turning off the strict input validation
        gate_instruction = UnitaryGate(matrix_data, check_input=False)
        
        controlled_U_power = gate_instruction.control(
            num_ctrl_qubits=1
        )   
  

        circuit.append(
            controlled_U_power,
            [phase_qubit[0]] + list(system)
        )

        # ----------------------------------------------------
        # Phase feedback
        #
        # This generic circuit construction uses a classical
        # conditional phase correction based on previously
        # measured bits.
        #
        # The actual angle is:
        #
        #   -2π * 0.b_(k+1)b_(k+2)...b_(m-1)
        #
        # ----------------------------------------------------

        if k < precision - 1:

            # Apply conditional corrections for previously
            # measured bits.
            #
            # The exact feedback convention depends on whether
            # bits are processed MSB -> LSB or LSB -> MSB.
            #
            # We use a direct classical-condition construction.

            for j in range(k + 1, precision):

                angle = -math.pi / (2 ** (j - k))

                # Use Qiskit's modern conditional block syntax
                with circuit.if_test((phase_bits[j], 1)):
                    circuit.p(angle, phase_qubit[0])

        # ----------------------------------------------------
        # Final Hadamard
        # ----------------------------------------------------

        circuit.h(phase_qubit[0])

        # ----------------------------------------------------
        # Measure the current phase bit
        # ----------------------------------------------------

        circuit.measure(
            phase_qubit[0],
            phase_bits[k]
        )

    return circuit