"""
Run Grover's search on hardware with full error mitigation: dynamical
decoupling + twirling + zero-noise extrapolation (ZNE) + M3 readout
mitigation.

Mirrors the notebook's "Run Grover's search on hardware with full
mitigation" cell.

Usage:
    python scripts/run_grover_hardware_mitigated.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from qiskit import ClassicalRegister
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

from qc_pipeline.hardware.backend_selection import select_backend
from qc_pipeline.hardware.mitigation import (
    make_mitigated_sampler,
    fold_circuit_global,
    m3_mitigate_counts,
    zne_extrapolate,
)
from qc_pipeline.grover.decode import key_to_bitstring


def run_mitigated_grover(OracleSpace, key, width_qubits, height_qubits, search_qubits_count,
                          backend=None, scale_factors=(1, 3, 5), shots=4096):
    if backend is None:
        backend = select_backend(min_num_qubits=search_qubits_count + 3)

    search_qubit_list = list(range(search_qubits_count))

    mitigated_sampler = make_mitigated_sampler(backend)
    pm = generate_preset_pass_manager(backend=backend, optimization_level=3)

    # Target bitstring for the key (Qiskit orders qubit (n-1) leftmost)
    target_bitstring = key_to_bitstring(key, width_qubits, height_qubits)
    print(f"Target bitstring: {target_bitstring}")

    target_probs_by_scale = []
    for sf in scale_factors:
        unmeasured = OracleSpace.copy()
        folded = fold_circuit_global(unmeasured, sf)
        folded.add_register(ClassicalRegister(search_qubits_count, name="result"))
        folded.measure(search_qubit_list, folded.cregs[0])

        isa_folded = pm.run(folded)
        job = mitigated_sampler.run([isa_folded], shots=shots)
        result = job.result()
        raw_counts = result[0].data.result.get_counts()

        mitigated_probs = m3_mitigate_counts(raw_counts, backend, search_qubit_list)
        p_target = mitigated_probs.get(target_bitstring, 0.0)
        target_probs_by_scale.append(p_target)
        print(
            f"scale={sf}: P(target)={p_target:.4f}  "
            f"(raw shots at target: {raw_counts.get(target_bitstring, 0)})"
        )

    zne_estimate, coeffs = zne_extrapolate(list(scale_factors), target_probs_by_scale, order=1)
    print(f"\nZero-noise-extrapolated P(target key found) = {zne_estimate:.4f}")

    return list(scale_factors), target_probs_by_scale, zne_estimate


if __name__ == "__main__":
    from scripts.run_grover_pipeline import run_grover_pipeline

    OracleSpace, key, _, width_qubits, height_qubits, search_qubits_count = run_grover_pipeline()
    run_mitigated_grover(OracleSpace, key, width_qubits, height_qubits, search_qubits_count)
