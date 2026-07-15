from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

import customise


def get_service():
    """
    Builds the runtime service from customise.py credentials if provided,
    otherwise falls back to locally saved account credentials.
    """
    if customise.IBM_API_KEY:
        kwargs = {"channel": "ibm_quantum_platform", "token": customise.IBM_API_KEY}
        if customise.IBM_INSTANCE_CRN:
            kwargs["instance"] = customise.IBM_INSTANCE_CRN
        return QiskitRuntimeService(**kwargs)
    return QiskitRuntimeService()


def select_backend(service, min_num_qubits, backend_name=None):
    if backend_name is not None:
        return service.backend(backend_name)
    try:
        return service.least_busy(
            operational=True, simulator=False, min_num_qubits=min_num_qubits
        )
    except Exception:
        print("[WARNING] service.least_busy failed. Falling back to manual backend discovery...")

        available_backends = service.backends(simulator=False, operational=True)
        suitable_backends = [
            b for b in available_backends if b.num_qubits >= min_num_qubits
        ]

        if not suitable_backends:
            raise RuntimeError(
                f"Could not find any operational hardware backend with at least {min_num_qubits} qubits."
            )

        return suitable_backends[0]


def submit_to_hardware(qc, service=None, backend=None, shots=4096, min_num_qubits=None,
                        backend_name=None, optimization_level=3):
    """
    Transpiles and submits a circuit to real IBM Quantum hardware.
    """
    if service is None:
        service = get_service()

    if min_num_qubits is None:
        min_num_qubits = qc.num_qubits

    if backend is None:
        backend = select_backend(service, min_num_qubits, backend_name)

    print(f"Using real hardware backend: {backend.name} ({backend.num_qubits} qubits)")

    pm = generate_preset_pass_manager(backend=backend, optimization_level=optimization_level)
    isa_circuit = pm.run(qc)

    sampler = Sampler(mode=backend)
    sampler.options.default_shots = shots

    job = sampler.run([isa_circuit])
    return job, isa_circuit, backend
