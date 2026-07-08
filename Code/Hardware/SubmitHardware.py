from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

def submit_to_hardware(qc, shots=4096, min_num_qubits=None, backend_name=None,
                       optimization_level=3):
    """
    Transpiles and submits a circuit to real IBM Quantum hardware.
    Robustly handles backend filtering and avoids non-ASCII character errors.
    """
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