#External Imports
from qiskit.circuit import QuantumRegister, QuantumCircuit
#Internal Connections
from FilePipeline.Internal.DimensionGen import *

def CreateSpace(N):
	w,h = CreateDimension(N)
	QRWidth = QuantumRegister(w, name = "Width")
	QRHeight = QuantumRegister(h, name = "Height")
	QC = QuantumCircuit(QRWidth, QRHeight)
	return QC, [w,h]
