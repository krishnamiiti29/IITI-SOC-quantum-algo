"""
Quantum (QPE) order-finding demo: test the QPE circuit on AerSimulator
first, then optionally run the same small N on real IBM Quantum hardware.

Mirrors the notebook's cells 6-8.

Usage:
    python scripts/run_qpe_demo.py                 # simulator only
    python scripts/run_qpe_demo.py --hardware       # also run on real hardware
    python scripts/run_qpe_demo.py --N 6 --hardware
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from qc_pipeline.quantum_order_finding.qpe_runner import ProvideDimensionsQuantum
from qc_pipeline.hardware.backend_selection import select_backend, qpe_qubits_needed


def run_qpe_demo(test_N=4, use_hardware=False, sim_shots=8, hw_shots=64):
    # Test on the simulator first -- verify the QPE circuit itself works
    # before spending real hardware shots. Start with a SMALL N (e.g. 4, 6,
    # 9) since qubit count and circuit depth grow fast:
    # total qubits = n + t = n + (2n + 3).
    dims, gamma_used, order_found = ProvideDimensionsQuantum(test_N, backend=None, shots=sim_shots)
    print(f"N={test_N}, Gamma={gamma_used}, order found={order_found}, dims={dims}")

    if not use_hardware:
        return dims, gamma_used, order_found

    # Real backends have 100+ qubits, comfortably more than the QPE circuit
    # needs, so sizing only for the QPE circuit here is safe in practice.
    backend = select_backend(min_num_qubits=qpe_qubits_needed(test_N))

    # WARNING: unitary synthesis for controlled-U^(2^k) gates gets very deep
    # even for small N -- expect this to need many more shots (noise) than
    # the simulator to succeed. Start with the smallest N in NUMBER_CHOICES,
    # not a large one.
    dims_hw, gamma_hw, order_hw = ProvideDimensionsQuantum(test_N, backend=backend, shots=hw_shots)
    print(f"N={test_N}, Gamma={gamma_hw}, order found={order_hw}, dims={dims_hw}")
    return dims_hw, gamma_hw, order_hw


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--N", type=int, default=4, help="N to factor (default: 4)")
    parser.add_argument("--hardware", action="store_true", help="Also run on real IBM hardware")
    parser.add_argument("--sim-shots", type=int, default=8)
    parser.add_argument("--hw-shots", type=int, default=64)
    args = parser.parse_args()

    run_qpe_demo(
        test_N=args.N,
        use_hardware=args.hardware,
        sim_shots=args.sim_shots,
        hw_shots=args.hw_shots,
    )
