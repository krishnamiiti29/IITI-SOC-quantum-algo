from FilePipeline.Shors_Algorithm.FindFactor import recover_factors
from FilePipeline.Shors_Algorithm.IQPE.ClassicalPostProcess import estimate_order_from_counts
from FilePipeline.Phases.Phase1 import *
from FilePipeline.Shors_Algorithm.IQPE.CircuitGen import *
from FilePipeline.Shors_Algorithm.BuildUnitary import *
from FilePipeline.Shors_Algorithm.Setup import *

from qiskit_aer import AerSimulator
from qiskit import transpile
import sys
import io


def ApplyPhase1(N):
	CalculatedDimensions = []

	Gamma = ChooseGamma(N)
	precision = 8
	U = BuildUnitary(Gamma, N)

	iqpe_circuit = build_iqpe_circuit(
    U=U,
    precision=precision
	)


	# Your working draw line will now work perfectly

	simulator = AerSimulator()

	# 🛠️ FIX: Transpile the circuit for the simulator backend
	# This unpacks 'c-unitary' into standard simulator gates
	transpiled_circuit = transpile(iqpe_circuit, backend=simulator)

	# Run the transpiled circuit instead of the raw one
	job = simulator.run(
	    transpiled_circuit,
	    shots=1024
	)

	result = job.result()

	counts = result.get_counts()

	print(counts)

	recovered_order = estimate_order_from_counts(counts, Gamma, N)


	factors = recover_factors(
	    Gamma,
	    N,
	    recovered_order
	)

	if factors is not None:
		# Cleanly sort the tuple without modifying it inline
		if factors[0] > factors[1]:
			factors = (factors[1], factors[0])
            
		print("Factors:", factors)
		return factors
	else:
		print(f"Factors: None (Shor's algorithm failed to find factors for order r = {recovered_order} on this run).")
		return None

