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



NUM_RUNS = 3
classical_register_name = "phase_meas"

# 1. Setup Parameters and Get Mathematical Ground Truth
# Assuming Initiate() gives us the target dimensions/factors we want to match
true_dimensions, N = Initiate()   
n_work = int(np.ceil(np.log2(N)))   
valid_gammas = [i for i in range(2, N) if math.gcd(i, N) == 1]
gamma = random.choice(valid_gammas)

true_r = 1
print(f"\n=== System Parameters ===")
print(f"Modulus N = {N}, Base gamma = {gamma}")
print(f"True Order/Period: r = {true_r}")
print(f"Target Dimensions/Factors: {sorted(true_dimensions)}")
print(f"=========================\n")

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
    print(f"Hardware Measured Counts: {counts}")
    print(f"Hardware Calculated Order: r = {estimated_r}")

    # Compute calculated dimensions
    calc_dim1, calc_dim2 = calculate_dimensions_from_order(estimated_r, gamma, N)
    calculated_dimensions = [calc_dim1, calc_dim2] if calc_dim1 is not None else None
    print(f"Hardware Calculated Dimensions: {calculated_dimensions}")

    # Compare calculated dimensions to target dimensions
    if calculated_dimensions == sorted(true_dimensions):
        print("Result: CORRECT (Dimensions found match target)")
        correct_count += 1
    else:
        print("Result: WRONG (Failed to extract correct dimensions)")
        wrong_count += 1

# 4. Graphing the Performance Breakdown
print(f"\nFinal Real Hardware Tally -> Correct Factors: {correct_count}, Wrong Factors: {wrong_count}")

categories = ['Correct Dimensions', 'Wrong Dimensions']
values = [correct_count, wrong_count]
colors = ['#00b4d8', '#ff4d6d'] 

plt.figure(figsize=(6, 5))
bars = plt.bar(categories, values, color=colors, width=0.5)

plt.title(f"Shor's Dimension Extraction Success Rate\n(Target Dimensions = {sorted(true_dimensions)}, N={N})", fontsize=11, fontweight='bold')
plt.ylabel('Number of Hardware Executions', fontsize=10)
plt.ylim(0, NUM_RUNS + 1)
plt.grid(axis='y', linestyle=':', alpha=0.6)

for bar in bars:
    height = bar.get_height()
    plt.annotate(f'{height}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 4),  
                textcoords="offset points",
                ha='center', va='bottom', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.show()