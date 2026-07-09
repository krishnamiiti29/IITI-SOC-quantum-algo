"""
IBM Quantum backend selection.

Generalized from the notebook's "Select the IBM backend" and "Run OracleSpace
on real IBM Quantum hardware" cells, which both did:
  service = QiskitRuntimeService()
  backend = service.least_busy(operational=True, simulator=False, min_num_qubits=...)
"""


def select_backend(min_num_qubits):
    """
    Load the saved IBM Quantum Platform account and select the least-busy
    operational real backend with at least `min_num_qubits` qubits.

    Requires a saved account -- see hardware.save_account.save_ibm_account().
    """
    from qiskit_ibm_runtime import QiskitRuntimeService

    service = QiskitRuntimeService()  # loads saved account, including its CRN
    backend = service.least_busy(
        operational=True,
        simulator=False,
        min_num_qubits=min_num_qubits,
    )
    print(f"Selected backend: {backend.name} ({backend.num_qubits} qubits available)")
    return backend


def qpe_qubits_needed(N):
    """Total qubits (work + counting register) needed for the QPE order-finding circuit on N."""
    import numpy as np

    n = int(np.ceil(np.log2(N)))
    return n + (2 * n + 3)


def save_ibm_account(token, instance, channel="ibm_quantum_platform"):
    """
    One-time setup: save IBM Quantum Platform credentials locally.

    `instance` (CRN) is REQUIRED -- without it, save_account/QiskitRuntimeService
    tries to auto-discover instances via a search call that can fail.
    Get both from https://quantum.cloud.ibm.com
    (dashboard = API key, Instances tab = CRN).

    Run this once, then rely on the saved account thereafter.
    """
    from qiskit_ibm_runtime import QiskitRuntimeService

    QiskitRuntimeService.save_account(
        channel=channel,
        token=token,
        instance=instance,
        set_as_default=True,
        overwrite=True,
    )
