from qiskit.circuit import QuantumRegister, QuantumCircuit

from Internal.DimensionGen import *


def CreateSpace(N):
    w, h = CreateDimension(N)
    QRWidth = QuantumRegister(w, name="Width")
    QRHeight = QuantumRegister(h, name="Height")
    QC = QuantumCircuit(QRWidth, QRHeight)
    return QC, [w, h]


def CreateSpaceDimensioned(Width, Height):
    QRWidth = QuantumRegister(Width, name="Width")
    QRHeight = QuantumRegister(Height, name="Height")
    QC = QuantumCircuit(QRWidth, QRHeight)
    return QC, QRWidth, QRHeight