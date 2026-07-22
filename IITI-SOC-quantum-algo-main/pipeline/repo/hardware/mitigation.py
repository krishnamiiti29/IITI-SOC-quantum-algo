
import numpy as np
from qiskit import ClassicalRegister
from qiskit_ibm_runtime import SamplerV2

from hardware.execution.decode import key_to_bitstring


def make_mitigated_sampler(backend):
    """SamplerV2 configured with dynamical decoupling + gate/measurement twirling."""
    sampler = SamplerV2(mode=backend)
    sampler.options.dynamical_decoupling.enable = True
    sampler.options.dynamical_decoupling.sequence_type = "XY4"
    sampler.options.twirling.enable_gates = True
    sampler.options.twirling.enable_measure = True
    sampler.options.twirling.num_randomizations = "auto"
    return sampler


def fold_circuit_global(circuit, scale_factor):
    """Unitary folding for ZNE: U -> U (U^-1 U)^k, scale_factor = 2k+1.
    Circuit must NOT contain measurements."""
    if scale_factor == 1:
        return circuit.copy()
    assert (scale_factor - 1) % 2 == 0, "scale_factor must be odd (1, 3, 5, ...)"
    k = (scale_factor - 1) // 2
    folded = circuit.copy()
    for _ in range(k):
        folded = folded.compose(circuit.inverse())
        folded = folded.compose(circuit)
    return folded


def m3_mitigate_counts(counts, backend, qubits):
    """Matrix-free measurement mitigation: calibrates per-qubit readout error
    on the backend, then corrects the raw counts for that confusion."""
    import mthree
    mit = mthree.M3Mitigation(backend)
    mit.cals_from_system(qubits)
    quasi = mit.apply_correction(counts, qubits)
    return quasi.nearest_probability_distribution()


def zne_extrapolate(scale_factors, target_probs, order=1):
    """Fit probability-vs-noise-scale and extrapolate back to zero noise (scale=0)."""
    coeffs = np.polyfit(scale_factors, target_probs, order)
    zero_noise_estimate = np.polyval(coeffs, 0)
    return zero_noise_estimate, coeffs


def run_grover_with_mitigation(OracleSpace, backend, pm, search_qubits_count, key,
                                width_qubits, height_qubits, scale_factors=(1, 3, 5), shots=4096):
    """Run Grover's search on hardware with full mitigation: DD + twirling + ZNE + M3."""
    search_qubit_list = list(range(search_qubits_count))
    mitigated_sampler = make_mitigated_sampler(backend)

    target_bitstring = key_to_bitstring(key, width_qubits, height_qubits)
    print(f"Target bitstring: {target_bitstring}")

    target_probs_by_scale = []
    raw_counts_by_scale = []
    for sf in scale_factors:
        unmeasured = OracleSpace.copy()
        folded = fold_circuit_global(unmeasured, sf)
        folded.add_register(ClassicalRegister(search_qubits_count, name='result'))
        folded.measure(search_qubit_list, folded.cregs[0])

        isa_folded = pm.run(folded)
        job = mitigated_sampler.run([isa_folded], shots=shots)
        result = job.result()
        raw_counts = result[0].data.result.get_counts()

        mitigated_probs = m3_mitigate_counts(raw_counts, backend, search_qubit_list)
        p_target = mitigated_probs.get(target_bitstring, 0.0)
        target_probs_by_scale.append(p_target)
        raw_counts_by_scale.append(dict(raw_counts))
        print(f"scale={sf}: P(target)={p_target:.4f}  (raw shots at target: {raw_counts.get(target_bitstring, 0)})")

    zne_estimate, coeffs = zne_extrapolate(scale_factors, target_probs_by_scale, order=1)
    print(f"Zero-noise-extrapolated P(target key found) = {zne_estimate:.4f}")
    return zne_estimate, target_probs_by_scale, raw_counts_by_scale