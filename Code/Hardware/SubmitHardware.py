import os
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

MY_IBM_API_KEY = "cL3TvydWUlcyfKhqUpfuM8RP6q3A9msBA40JCzWmAt9g"


def submit_to_hardware(qc, shots=4096, min_num_qubits=None, backend_name=None,
                       optimization_level=3):
    """
    Transpiles and submits a circuit to real IBM Quantum hardware.
    Robustly handles backend filtering and avoids non-ASCII character errors.
    """
    # Initialize the service using the variable defined at the top
    if MY_IBM_API_KEY and MY_IBM_API_KEY != "PASTE_YOUR_NEW_IBM_QUANTUM_API_KEY_HERE":
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=MY_IBM_API_KEY)
    else:
        # Fallback to local disk credentials if the variable above wasn't updated
        print("[INFO] No valid API key found at the top variable. Checking local disk credentials...")
        service = QiskitRuntimeService()

    if min_num_qubits is None:
        min_num_qubits = qc.num_qubits

    if backend_name is not None:
        backend = service.backend(backend_name)
    else:
        try:
            # First attempt: standard dynamic selection
            backend = service.least_busy(
                operational=True, simulator=False, min_num_qubits=min_num_qubits
            )
        except Exception:
            print("[WARNING] service.least_busy failed. Falling back to manual backend discovery...")
            
            # Manually filter active public backends with >= min_num_qubits
            available_backends = service.backends(simulator=False, operational=True)
            suitable_backends = [
                b for b in available_backends if b.num_qubits >= min_num_qubits
            ]
            
            if not suitable_backends:
                raise RuntimeError(
                    f"Could not find any operational hardware backend with at least {min_num_qubits} qubits."
                )
            
            backend = suitable_backends[0]

    print(f"Using real hardware backend: {backend.name} ({backend.num_qubits} qubits)")

    pm = generate_preset_pass_manager(backend=backend, optimization_level=optimization_level)
    isa_circuit = pm.run(qc)

    sampler = Sampler(mode=backend)
    sampler.options.default_shots = shots

    # Submit job asynchronously
    job = sampler.run([isa_circuit])
    return job, isa_circuit
