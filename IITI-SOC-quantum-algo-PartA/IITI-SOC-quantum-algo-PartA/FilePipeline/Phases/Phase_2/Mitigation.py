"""
FilePipeline/Phases/Phase_2/Mitigation.py

Full error mitigation stack for the Phase 2 Grover search circuit,
run on real IBM Quantum hardware.

Applies in order:
  1. Dynamical decoupling (XY4) + gate/measurement twirling  -- on every job
  2. Zero-noise extrapolation (ZNE) via unitary folding       -- scale 1, 3, 5
  3. Matrix-free measurement error correction (M3)            -- per job

Returns the ZNE-extrapolated P(target key found) and the raw counts at
each scale factor for storage and plotting.

Nothing in Phase 1, Runner.py, EvenSuperposition.py, GenerateKey.py or
any other existing file is modified.
"""

import numpy as np
from qiskit import ClassicalRegister
from qiskit_ibm_runtime import SamplerV2
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager


# ── helpers ────────────────────────────────────────────────────────────────

def _key_to_bitstring(key, width, height):
    """Encode [key_x, key_y] as the bitstring the measurement register produces."""
    x_bits = format(key[0], f"0{width}b")[::-1]
    y_bits = format(key[1], f"0{height}b")[::-1]
    return (x_bits + y_bits)[::-1]


def _make_mitigated_sampler(backend):
    """SamplerV2 with DD (XY4) + gate/measurement twirling enabled."""
    sampler = SamplerV2(mode=backend)
    sampler.options.dynamical_decoupling.enable = True
    sampler.options.dynamical_decoupling.sequence_type = "XY4"
    sampler.options.twirling.enable_gates = True
    sampler.options.twirling.enable_measure = True
    sampler.options.twirling.num_randomizations = "auto"
    return sampler


def _fold_circuit(circuit, scale_factor):
    """
    Unitary folding for ZNE: U -> U (U^-1 U)^k, scale_factor = 2k+1.
    Circuit must NOT contain measurements.
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


def _m3_correct(counts, backend, qubits):
    """Matrix-free M3 measurement error correction."""
    import mthree
    mit = mthree.M3Mitigation(backend)
    mit.cals_from_system(qubits)
    quasi = mit.apply_correction(counts, qubits)
    return quasi.nearest_probability_distribution()


def _zne_extrapolate(scale_factors, probs, order=1):
    """Linear fit through (scale, P(target)) points, extrapolate to scale=0."""
    coeffs = np.polyfit(scale_factors, probs, order)
    return float(np.polyval(coeffs, 0)), coeffs


# ── main entry point ───────────────────────────────────────────────────────

def RunWithMitigation(GroverCircuit, backend, key, width, height,
                      scale_factors=(1, 3, 5), shots=4096):
    """
    Run the Grover search circuit on real IBM hardware with the full
    DD + twirling + ZNE + M3 mitigation stack.

    Parameters
    ----------
    GroverCircuit : QuantumCircuit
        The assembled Grover circuit WITHOUT measurements.
    backend       : IBM backend object (already selected)
    key           : [key_x, key_y]
    width         : int  -- number of width qubits
    height        : int  -- number of height qubits
    scale_factors : tuple of odd ints for ZNE noise scaling
    shots         : int

    Returns
    -------
    zne_estimate        : float -- ZNE-extrapolated P(target key)
    target_probs        : list  -- P(target) at each scale factor (post M3)
    raw_counts_by_scale : list  -- raw count dicts at each scale factor
    """
    search_qubits = list(range(width + height))
    target_bitstring = _key_to_bitstring(key, width, height)
    print(f"  Target bitstring: {target_bitstring}")

    pm = generate_preset_pass_manager(backend=backend, optimization_level=3)
    sampler = _make_mitigated_sampler(backend)

    target_probs        = []
    raw_counts_by_scale = []

    for sf in scale_factors:
        print(f"\n  [ZNE] Submitting scale_factor={sf}...")

        # Fold the unmeasured circuit
        folded = _fold_circuit(GroverCircuit, sf)

        # Add measurement
        creg = ClassicalRegister(len(search_qubits), name="result")
        folded.add_register(creg)
        folded.measure(search_qubits, creg)

        # Transpile and submit
        isa = pm.run(folded)
        job = sampler.run([isa], shots=shots)
        print(f"  Job submitted. ID: {job.job_id()}")
        result = job.result()
        raw_counts = result[0].data.result.get_counts()

        # M3 correction
        mitigated = _m3_correct(raw_counts, backend, search_qubits)
        p_target  = mitigated.get(target_bitstring, 0.0)

        print(f"  scale={sf}: P(target)={p_target:.4f}  "
              f"raw shots at target={raw_counts.get(target_bitstring, 0)}")

        target_probs.append(p_target)
        raw_counts_by_scale.append(dict(raw_counts))

    # ZNE extrapolation
    zne_estimate, _ = _zne_extrapolate(list(scale_factors), target_probs)
    print(f"\n  ZNE extrapolated P(target key found) = {zne_estimate:.4f}")

    return zne_estimate, target_probs, raw_counts_by_scale
