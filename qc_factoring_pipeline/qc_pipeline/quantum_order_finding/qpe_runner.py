"""
Quantum replacement for ProvideDimensions(): runs the QPE order-finding
circuit on either AerSimulator or a real IBM backend, and recovers a
nontrivial factor pair of N from the measured phase.

Extracted from the notebook's "Quantum replacement for ProvideDimensions()" cell.
"""

import math
import random

from qiskit import transpile
from qiskit_aer import AerSimulator

from qc_pipeline.quantum_order_finding.qpe_circuit import (
    BuildQPEOrderFindingCircuit,
    PhaseToOrder,
)


def ProvideDimensionsQuantum(N, backend=None, shots=8):
    """
    Quantum (QPE-based) order finding to recover a nontrivial factor pair
    of N.

    backend=None runs on AerSimulator (test this first); pass a real IBM
    backend to run on hardware.

    Returns:
        (factor_pair_or_None, Gamma, order_or_None)
    """
    valid_Gamma = [i for i in range(2, N) if math.gcd(i, N) == 1]
    Gamma = random.choice(valid_Gamma)

    qpe_circuit, t = BuildQPEOrderFindingCircuit(Gamma, N)
    print(f"Gamma={Gamma}, counting qubits={t}, total qubits={qpe_circuit.num_qubits}")

    if backend is None:
        sim = AerSimulator()
        compiled = transpile(qpe_circuit, sim)
        result = sim.run(compiled, shots=shots).result()
        counts = result.get_counts()
    else:
        # Local imports: qiskit_ibm_runtime is only needed for real hardware runs.
        from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
        from qiskit_ibm_runtime import SamplerV2

        pm = generate_preset_pass_manager(backend=backend, optimization_level=3)
        isa = pm.run(qpe_circuit)
        print(f"Transpiled depth: {isa.depth()}, gate count: {isa.size()}")
        sampler = SamplerV2(mode=backend)
        job = sampler.run([isa], shots=shots)
        result = job.result()
        counts = result[0].data.c.get_counts()

    # try measured outcomes most-frequent first
    for bitstring, _ in sorted(counts.items(), key=lambda kv: -kv[1]):
        measured_int = int(bitstring, 2)
        if measured_int == 0:
            continue
        r = PhaseToOrder(measured_int, t, N)
        if r == 0 or r % 2 != 0:
            continue
        x = pow(int(Gamma), r // 2, int(N))
        if x == 1:
            continue
        for f in (math.gcd(N, x + 1), math.gcd(N, x - 1)):
            if f > 1 and N % f == 0:
                other = N // f
                if other > 1:
                    return (f, other), Gamma, r
    return None, Gamma, None
