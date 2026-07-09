"""
Run the OracleSpace circuit (from run_grover_pipeline) on real IBM Quantum
hardware, then retrieve and decode the results.

Mirrors the notebook's cells 17-18.

Usage:
    python scripts/run_grover_hardware.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from qiskit import ClassicalRegister
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import SamplerV2

from qc_pipeline.hardware.backend_selection import select_backend
from qc_pipeline.grover.decode import decode_counts


def submit_hardware_job(OracleSpace, search_qubits_count, backend=None, shots=2048):
    """Build the measured circuit, transpile to the backend's ISA, and submit. Mirrors cell 17."""
    if backend is None:
        backend = select_backend(min_num_qubits=search_qubits_count + 3)
    assert backend.num_qubits >= search_qubits_count + 3, (
        f"Selected backend only has {backend.num_qubits} qubits, need {search_qubits_count + 3}"
    )
    print(f"Running on: {backend.name}")

    hw_circuit = OracleSpace.copy()
    creg = ClassicalRegister(search_qubits_count, name="result")
    hw_circuit.add_register(creg)
    hw_circuit.measure(list(range(search_qubits_count)), creg)

    pm = generate_preset_pass_manager(backend=backend, optimization_level=3)
    isa_circuit = pm.run(hw_circuit)
    print(f"Transpiled depth: {isa_circuit.depth()}, gate count: {isa_circuit.size()}")

    sampler = SamplerV2(mode=backend)
    job = sampler.run([isa_circuit], shots=shots)
    print(f"Job ID: {job.job_id()}")
    print(f"Job status: {job.status()}")
    return job, backend


def retrieve_hardware_results(job, key, width_qubits, height_qubits):
    """
    Retrieve and decode hardware results. Mirrors cell 18.

    NOTE: job.status() must show DONE before calling this -- this can take
    minutes to hours depending on queue.
    """
    hw_result = job.result()
    hw_counts = hw_result[0].data.result.get_counts()

    decoded_hw_counts = decode_counts(hw_counts, width_qubits, height_qubits)
    sorted_hw_results = sorted(decoded_hw_counts.items(), key=lambda kv: -kv[1])

    print(f"Target key: {key}")
    print("Top measured (x, y) pairs on real hardware:")
    for (x_val, y_val), count in sorted_hw_results[:10]:
        marker = " <-- TARGET" if [x_val, y_val] == key else ""
        print(f"  ({x_val}, {y_val}): {count} shots{marker}")

    return decoded_hw_counts


if __name__ == "__main__":
    from scripts.run_grover_pipeline import run_grover_pipeline

    OracleSpace, key, _, width_qubits, height_qubits, search_qubits_count = run_grover_pipeline()
    job, backend = submit_hardware_job(OracleSpace, search_qubits_count)
    print("Submitted. Once job.status() == 'DONE', call retrieve_hardware_results(job, key, "
          "width_qubits, height_qubits) to decode results.")
