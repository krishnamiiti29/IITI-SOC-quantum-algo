# Import Block
# pip install qiskit
# pip install qiskit_aer
# pip install matplotlib
import math
import random
import time
import numpy as np
import matplotlib.pyplot as plt
from fractions import Fraction
from Initiate import *
from Unitary.UnitaryFunc import *
from Unitary.UnitaryOp import *
from Hardware.ExtractOrder import *
from Hardware.SubmitHardware import *
from CalculateDimension import *
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

NUM_RUNS = 1
classical_register_name = "phase_meas"

#Ensure target true_dimensions are sorted for accurate list-to-list matching
true_dimensions, N = Initiate()
target_dimensions = sorted([d for d in true_dimensions if d is not None])

n_work = int(np.ceil(np.log2(N)))
valid_gammas = [i for i in range(2, N) if math.gcd(i, N) == 1]
gamma = random.choice(valid_gammas)
U = BuildUnitary(gamma, N)

# 2. Batch Submit Jobs to Hardware Queue
jobs_list = []
print(f"Submitting {NUM_RUNS} jobs to IBM Quantum hardware...")
for run in range(1, NUM_RUNS + 1):
    print(f"\n[Submission {run}/{NUM_RUNS}] Building and routing circuit...")
    qc, t_phase = build_qpe_circuit(U, n_work, N, gamma, add_measurement=True)
    job, isa_circuit = submit_to_hardware(qc, shots=4096)
    print(f"Job {run} submitted successfully. ID: {job.job_id()}")
    jobs_list.append((run, job, t_phase))

print("\nAll jobs successfully sent to the IBM Quantum cluster. Monitoring status...")

# 3. Retrieve Results and Process
correct_count = 0
wrong_count = 0

for run, job, t_phase in jobs_list:
    print(f"\nRetrieving results for Run {run}/{NUM_RUNS} (Job ID: {job.job_id()})...")
    print("Waiting for job to finish executing (this blocks until complete)...")
    result = job.result()
    pub_result = result[0]
    counts = getattr(pub_result.data, classical_register_name).get_counts()
    
    # Process order finding
    estimated_r = extract_order_from_counts(counts, t_phase, N, gamma)
    
    #Compute calculated dimensions
    calc_dim1, calc_dim2 = calculate_dimensions_from_order(estimated_r, gamma, N)
    
    # Clean, filter out None values, and sort the hardware dimensions for matching
    calculated_dimensions = sorted([d for d in [calc_dim1, calc_dim2] if d is not None])
    print(f"Hardware Calculated Dimensions: {calculated_dimensions}")
