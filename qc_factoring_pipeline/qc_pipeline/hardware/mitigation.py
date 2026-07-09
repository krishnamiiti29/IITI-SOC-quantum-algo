"""
Advanced error mitigation toolkit: dynamical decoupling + twirling sampler,
unitary folding for zero-noise extrapolation (ZNE), M3 readout mitigation,
and the ZNE extrapolation fit itself.

Requires: pip install mthree

Extracted from the notebook's "Advanced error mitigation toolkit" cell.
"""

import numpy as np


def make_mitigated_sampler(backend):
    """SamplerV2 configured with dynamical decoupling + gate/measurement twirling."""
    from qiskit_ibm_runtime import SamplerV2

    sampler = SamplerV2(mode=backend)
    # Dynamical decoupling: inserts pulse sequences into idle qubit time to
    # suppress dephasing from the environment.
    sampler.options.dynamical_decoupling.enable = True
    sampler.options.dynamical_decoupling.sequence_type = "XY4"
    # Twirling: randomizes gate/readout errors into stochastic (easier to
    # average out) noise instead of fixed coherent errors.
    sampler.options.twirling.enable_gates = True
    sampler.options.twirling.enable_measure = True
    sampler.options.twirling.num_randomizations = "auto"
    return sampler


def fold_circuit_global(circuit, scale_factor):
    """
    Unitary folding for ZNE: U -> U (U^-1 U)^k, scale_factor = 2k+1.
    Amplifies the noise while preserving the ideal unitary (up to the added
    noise). Circuit must NOT contain measurements.
    """
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
    """
    Matrix-free measurement mitigation: calibrates per-qubit readout error
    on the backend, then corrects the raw counts for that confusion.
    """
    import mthree

    mit = mthree.M3Mitigation(backend)
    mit.cals_from_system(qubits)
    quasi = mit.apply_correction(counts, qubits)
    return quasi.nearest_probability_distribution()


def zne_extrapolate(scale_factors, target_probs, order=1):
    """
    Fit probability-vs-noise-scale and extrapolate back to zero noise
    (scale=0). order=1 (linear/Richardson) is safest with only 3 points;
    use order=2 if a 4th+ scale factor is added and curvature is visible.
    """
    coeffs = np.polyfit(scale_factors, target_probs, order)
    zero_noise_estimate = np.polyval(coeffs, 0)
    return zero_noise_estimate, coeffs
