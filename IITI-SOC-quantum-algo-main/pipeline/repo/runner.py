import math
import random
import numpy as np
from qiskit import ClassicalRegister

from internal.initiate import Initiate, GiveQubitCount, KeyChoice, GiveHammingWeight
from hardware.circuits.unitary import BuildUnitary
from hardware.circuits.qpe import build_qpe_circuit
from hardware.circuits.oracle import (
    CreateConstrainedEvenSuperposition,
    build_fixed_point_grover_circuit,
)
from hardware.execution.submit import get_service, submit_to_hardware
from hardware.execution.extract_order import extract_order_from_counts
from hardware.execution.calculate_dimension import calculate_dimensions_from_order
from hardware.execution.decode import decode_bitstring
from hardware.mitigation import run_grover_with_mitigation
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

NUM_RUNS = 1
CLASSICAL_REGISTER_NAME = "phase_meas"
GROVER_ITERATIONS = 8  # fixed-point pi/3 oracle+diffuser rounds; safe to set generously


def run_phase_1():
    Space, N = Initiate()

    n_work = int(np.ceil(np.log2(N)))
    valid_gammas = [i for i in range(2, N) if math.gcd(i, N) == 1]
    gamma = random.choice(valid_gammas)
    U = BuildUnitary(gamma, N)

    service = get_service()

    jobs_list = []
    backend = None
    print(f"Submitting {NUM_RUNS} jobs to IBM Quantum hardware...")
    for run in range(1, NUM_RUNS + 1):
        print(f"\n[Submission {run}/{NUM_RUNS}] Building and routing circuit...")
        qpe_circuit, t_phase = build_qpe_circuit(U, n_work, N, gamma, add_measurement=True)
        job, isa_circuit, backend = submit_to_hardware(qpe_circuit, service=service, backend=backend, shots=4096)
        print(f"Job {run} submitted successfully. ID: {job.job_id()}")
        jobs_list.append((run, job, t_phase))

    print("\nAll jobs successfully sent to the IBM Quantum cluster. Monitoring status...")

    calculated_dimensions = []
    for run, job, t_phase in jobs_list:
        print(f"\nRetrieving results for Run {run}/{NUM_RUNS} (Job ID: {job.job_id()})...")
        result = job.result()
        pub_result = result[0]
        counts = getattr(pub_result.data, CLASSICAL_REGISTER_NAME).get_counts()

        estimated_r = extract_order_from_counts(counts, t_phase, N, gamma)
        calc_dim1, calc_dim2 = calculate_dimensions_from_order(estimated_r, gamma, N)
        calculated_dimensions = sorted([d for d in [calc_dim1, calc_dim2] if d is not None])
        print(f"Hardware Calculated Dimensions: {calculated_dimensions}")

    Width, Height = calculated_dimensions[0], calculated_dimensions[1]
    print(f"Width is: {Width}, and Height is: {Height}")

    return Space, N, Width, Height, service, backend


def run_phase_2(Space, N, Width, Height, service, backend):
    width_qubits, height_qubits = GiveQubitCount([Width, Height])
    search_qubits_count = width_qubits + height_qubits

    EvenSpace = CreateConstrainedEvenSuperposition(Space, width_qubits, height_qubits)

    key = KeyChoice((Width, Height))
    print(f"Key: {key}")

    # Target parity the oracle marks: HW(x) XOR HW(y) mod 2, derived from
    # the actual key (rather than hardcoded), per the HW(x) XOR HW(y) rule.
    target_parity = (GiveHammingWeight(key[0]) ^ GiveHammingWeight(key[1])) % 2
    print(f"Target parity (HW(x) XOR HW(y) mod 2): {target_parity}")

    # Hamming Weight resonance oracle + fixed-point pi/3 Grover circuit.
    # Marks every (x,y) state satisfying HW(x) XOR HW(y) == target_parity,
    # with x constrained to even Hamming weight only -- per IITISoC spec.
    OracleSpace = build_fixed_point_grover_circuit(
        EvenSpace, width_qubits, height_qubits, target_parity,
        iterations=GROVER_ITERATIONS,
    )

    # Build the pass manager explicitly so we can hand it to
    # run_grover_with_mitigation (which needs it to transpile each
    # noise-scaled circuit before submission).
    print(f"\nPreparing Phase 2 (Grover search) with full error mitigation on: {backend.name}...")
    pm = generate_preset_pass_manager(backend=backend, optimization_level=3)

    # run_grover_with_mitigation handles everything:
    #   - dynamical decoupling + gate/measurement twirling (DD + twirling)
    #   - zero-noise extrapolation across scale factors (1, 3, 5) (ZNE)
    #   - matrix-free measurement error correction (M3)
    # It submits 3 separate jobs (one per scale factor), waits for each,
    # corrects the counts, then extrapolates back to zero noise.
    zne_estimate, target_probs_by_scale, raw_counts_by_scale = run_grover_with_mitigation(
        OracleSpace=OracleSpace,
        backend=backend,
        pm=pm,
        search_qubits_count=search_qubits_count,
        key=key,
        width_qubits=width_qubits,
        height_qubits=height_qubits,
        scale_factors=(1, 3, 5),
        shots=4096,
    )

    print(f"\nTarget key: {key}")
    print(f"P(target key found) at scale factors (1,3,5): {[round(p,4) for p in target_probs_by_scale]}")
    print(f"Zero-noise-extrapolated P(target key found): {zne_estimate:.4f}")

    found = zne_estimate >= 0.5
    print(f"Key {'FOUND' if found else 'BEST CANDIDATE (ZNE < 0.5 -- noise present)'}: {key}")

    return {
        "key":                  key,
        "width_qubits":         width_qubits,
        "height_qubits":        height_qubits,
        "search_qubits_count":  search_qubits_count,
        "target_parity":        target_parity,
        "zne_estimate":         zne_estimate,
        "target_probs_by_scale": list(target_probs_by_scale),
        "raw_counts_by_scale":  raw_counts_by_scale,   # list of 3 dicts (scale 1,3,5)
        "scale_factors":        [1, 3, 5],
    }


def main():
    Space, N, Width, Height, service, backend = run_phase_1()
    phase2 = run_phase_2(Space, N, Width, Height, service, backend)
    return {
        "N":            N,
        "Width":        Width,
        "Height":       Height,
        "backend_name": backend.name,
        **phase2,
    }


if __name__ == "__main__":
    main()