import sys
import math
from qiskit_aer import AerSimulator
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

from Shors_Algorithm.FindFactor import recover_factors
from Shors_Algorithm.IQPE.ClassicalPostProcess import estimate_order_from_counts
from Shors_Algorithm.IQPE.CircuitGen import *
from Shors_Algorithm.BuildUnitary import *
from Shors_Algorithm.Setup import *
from Customize import IBM_API_KEY, IBM_INSTANCE_CRN


def _get_backend(min_qubits):
    """Connect to IBM Quantum using credentials from Customize.py and
    pick the least busy backend that can fit this circuit."""
    kwargs = {"channel": "ibm_quantum_platform", "token": IBM_API_KEY}
    if IBM_INSTANCE_CRN:
        kwargs["instance"] = IBM_INSTANCE_CRN
    service = QiskitRuntimeService(**kwargs)
    return service.least_busy(simulator=False, operational=True, min_num_qubits=min_qubits)


def ApplyPhase1(N):
    Gamma = ChooseGamma(N)
    precision = 8
    U = BuildUnitary(Gamma, N)

    iqpe_circuit = build_iqpe_circuit(U=U, precision=precision)
    print(f"Logical circuit depth (fixed, uninformative): {iqpe_circuit.depth()}")

    # Hardware initialization with simulator fallback
    try:
        backend = _get_backend(precision)
        is_hardware = True
        print(f"Connected to IBM Quantum. Using backend: {backend.name}")
    except Exception as e:
        backend = AerSimulator()
        is_hardware = False
        print(f"Could not connect to hardware ({e}). Falling back to local AerSimulator.")

    pm = generate_preset_pass_manager(optimization_level=1, backend=backend)
    transpiled_circuit = pm.run(iqpe_circuit)

    print(f"Transpiled depth (real cost): {transpiled_circuit.depth()}")
    print(f"Transpiled gate counts: {transpiled_circuit.count_ops()}")

    if is_hardware:
        print(f"Submitting to IBM Quantum ({backend.name}) via SamplerV2...")
        sys.stdout.flush()

        sampler = SamplerV2(backend)
        job = sampler.run([transpiled_circuit], shots=1024)
        result = job.result()

        pub_result = result[0]
        reg_name = list(pub_result.data.keys())[0]
        counts = pub_result.data[reg_name].get_counts()
    else:
        job = backend.run(transpiled_circuit, shots=1024)
        result = job.result()
        counts = result.get_counts()

    print("Counts:", counts)

    recovered_order = estimate_order_from_counts(counts, Gamma, N)
    factors = recover_factors(Gamma, N, recovered_order)

    if factors is not None:
        if factors[0] > factors[1]:
            factors = (factors[1], factors[0])
        print("Factors:", factors)
        return factors

    print(f"Factors: None (Shor's algorithm failed to find factors for order r = {recovered_order} on this run).")
    return None