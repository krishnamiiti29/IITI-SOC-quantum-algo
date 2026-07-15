import math
import random
import numpy as np
from qiskit import ClassicalRegister, transpile
from qiskit_aer import AerSimulator

from internal.initiate import Initiate, GiveQubitCount, KeyChoice, GiveHammingWeight
from hardware.circuits.unitary import BuildUnitary
from hardware.circuits.qpe import build_qpe_circuit
from hardware.circuits.oracle import (
    CreateConstrainedEvenSuperposition,
    ApplyHammingWeightResonanceOracle,
    build_pi3_diffuser,
)
from hardware.execution.submit import get_service, submit_to_hardware
from hardware.execution.extract_order import extract_order_from_counts
from hardware.execution.calculate_dimension import calculate_dimensions_from_order
from hardware.execution.decode import decode_bitstring

NUM_RUNS = 1
CLASSICAL_REGISTER_NAME = "phase_meas"


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


def run_phase_2(Space, N, Width, Height):
    width_qubits, height_qubits = GiveQubitCount([Width, Height])
    search_qubits_count = width_qubits + height_qubits

    EvenSpace = CreateConstrainedEvenSuperposition(Space, N, width_qubits)

    key = KeyChoice((Width, Height))
    print(f"Key: {key}")
    print(GiveHammingWeight(key[0]) % 2, GiveHammingWeight(key[1]) % 2)

    EvenSpace.x(search_qubits_count + 2)
    EvenSpace.h(search_qubits_count + 2)

    OracleSpace = ApplyHammingWeightResonanceOracle(EvenSpace, width_qubits, search_qubits_count, 1)
    diffuser = build_pi3_diffuser(search_qubits_count)
    OracleSpace.append(diffuser, list(range(search_qubits_count)))

    sim_circuit = OracleSpace.copy()
    creg = ClassicalRegister(search_qubits_count, name='result')
    sim_circuit.add_register(creg)
    sim_circuit.measure(list(range(search_qubits_count)), creg)

    simulator = AerSimulator()
    compiled = transpile(sim_circuit, simulator)
    result = simulator.run(compiled, shots=2048).result()
    counts = result.get_counts()

    decoded_counts = {}
    for bitstring, count in counts.items():
        xy = decode_bitstring(bitstring, width_qubits, height_qubits)
        decoded_counts[xy] = decoded_counts.get(xy, 0) + count

    sorted_results = sorted(decoded_counts.items(), key=lambda kv: -kv[1])

    print(f"Target key: {key}")
    print("Top measured (x, y) pairs:")
    for (x_val, y_val), count in sorted_results[:45]:
        marker = " <-- TARGET" if [x_val, y_val] == key else ""
        print(f"  ({x_val}, {y_val}): {count} shots{marker}")

    return OracleSpace, key, width_qubits, height_qubits, search_qubits_count, decoded_counts


def main():
    Space, N, Width, Height, service, backend = run_phase_1()
    run_phase_2(Space, N, Width, Height)


if __name__ == "__main__":
    main()
