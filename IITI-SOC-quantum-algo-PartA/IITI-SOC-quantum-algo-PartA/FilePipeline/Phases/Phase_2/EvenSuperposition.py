from qiskit import QuantumCircuit, QuantumRegister
from FilePipeline.Internal.SpaceGen import *

def CreateEvenSuperposition(width, height):
    # Initialize the circuit and registers
    QC, QRWidth, QRHeight = CreateSpaceDimensioned(width, height)
    
    # 1. Create superposition for ALL height values
    for i in range(height):
        QC.h(QRHeight[i])
        
    # 2. Create superposition for EVEN width values
    # We apply Hadamard gates to all width qubits EXCEPT the least significant bit (index 0)
    # This leaves the LSB in the state |0>, forcing the overall value to be even
    for i in range(1, width):
        QC.h(QRWidth[i])
        
    return QC