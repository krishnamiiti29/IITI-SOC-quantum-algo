"""
Run QAOA against the VQF Hamiltonian, on simulator or real hardware.

On hardware, resilience_level=2 turns on IBM Runtime's BUILT-IN zero-noise
extrapolation for the Estimator -- more robust than hand-rolled folding, and
stacked with dynamical decoupling + twirling here too.

Extracted from the notebook's "Run QAOA against the VQF Hamiltonian" cell.
"""

import math

import numpy as np
from qiskit.circuit.library import QAOAAnsatz
from qiskit.primitives import StatevectorEstimator, StatevectorSampler
from scipy.optimize import minimize

from qc_pipeline.vqf.hamiltonian import build_vqf_hamiltonian


def run_vqf(N, backend=None, reps=2, maxiter=100, shots=4096):
    """
    Factor N using VQF/QAOA. Falls back to trial division if N is even or
    too small to have free search bits.

    Returns:
        (factor_pair_or_None, cost_history_or_None)
    """
    built = build_vqf_hamiltonian(N)
    if built is None:
        # N even, or too small to have free bits -- factor classically
        for f in range(2, int(math.isqrt(N)) + 1):
            if N % f == 0:
                print(f"N={N} factors trivially/classically: {(f, N // f)}")
                return (f, N // f), None
        return None, None

    hamiltonian, var_to_qubit, p_syms, q_syms, k = built
    ansatz = QAOAAnsatz(cost_operator=hamiltonian, reps=reps)
    cost_history = []

    if backend is None:
        estimator = StatevectorEstimator()
        sampler = StatevectorSampler()
    else:
        # Local imports: qiskit_ibm_runtime is only needed for real hardware runs.
        from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
        from qiskit_ibm_runtime import EstimatorV2, SamplerV2

        pm = generate_preset_pass_manager(backend=backend, optimization_level=3)
        ansatz = pm.run(ansatz)
        hamiltonian = hamiltonian.apply_layout(ansatz.layout)

        estimator = EstimatorV2(mode=backend)
        estimator.options.resilience_level = 2  # built-in ZNE
        estimator.options.dynamical_decoupling.enable = True
        estimator.options.dynamical_decoupling.sequence_type = "XY4"
        estimator.options.twirling.enable_gates = True

        sampler = SamplerV2(mode=backend)
        sampler.options.dynamical_decoupling.enable = True
        sampler.options.twirling.enable_gates = True
        sampler.options.twirling.enable_measure = True

    def cost_fn(params):
        job = estimator.run([(ansatz, hamiltonian, params)])
        cost = float(job.result()[0].data.evs)
        cost_history.append(cost)
        return cost

    x0 = np.random.uniform(0, np.pi, ansatz.num_parameters)
    result = minimize(cost_fn, x0, method="COBYLA", options={"maxiter": maxiter})

    final_circuit = ansatz.copy()
    final_circuit.measure_all()
    job = sampler.run([(final_circuit, result.x)], shots=shots)
    counts = job.result()[0].data.meas.get_counts()

    best_bitstring = max(counts, key=counts.get)
    bits = best_bitstring[::-1]

    def extract_value(syms, k, var_to_qubit, bits):
        val = 1 + (1 << (k - 1))  # LSB + MSB fixed to 1
        for i in range(1, k - 1):
            label = str(syms[i])
            if label in var_to_qubit:
                qidx = var_to_qubit[label]
                if qidx < len(bits) and bits[qidx] == "1":
                    val += (1 << i)
        return val

    p_val = extract_value(p_syms, k, var_to_qubit, bits)
    q_val = extract_value(q_syms, k, var_to_qubit, bits)

    print(f"Best bitstring: p={p_val}, q={q_val}, p*q={p_val * q_val}, target N={N}")
    if p_val * q_val == N and p_val > 1 and q_val > 1:
        return (p_val, q_val), cost_history
    print(
        "QAOA did not land on an exact factor pair -- try more reps/maxiter/shots, "
        "or raise `strength` in build_vqf_hamiltonian if constraints aren't enforced enough."
    )
    return None, cost_history
