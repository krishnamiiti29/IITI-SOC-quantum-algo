"""
Variational Quantum Factoring (VQF) demo: factor N with QAOA on the
simulator first, then optionally run the same N on real IBM Quantum
hardware.

Mirrors the notebook's cells 11-12. If --N is not given, N is generated via
the classical Phase 1 pipeline (scripts.run_classical_pipeline).

COST WARNING (hardware): each COBYLA iteration submits its own Estimator
job -- maxiter=40 means up to 40 separate hardware jobs, each with
resilience_level=2 (ZNE) which itself multiplies the underlying circuit
executions. Start with a small maxiter (10-20) before scaling up.

Usage:
    python scripts/run_vqf_demo.py --N 21
    python scripts/run_vqf_demo.py --N 21 --hardware --maxiter 20
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from qc_pipeline.vqf.runner import run_vqf
from qc_pipeline.hardware.backend_selection import select_backend


def run_vqf_demo(N, use_hardware=False, sim_maxiter=150, hw_maxiter=20, hw_shots=4096):
    print(f"Factoring actual N = {N} with VQF (simulator)...")
    vqf_dims_sim, vqf_cost_history_sim = run_vqf(N, backend=None, reps=2, maxiter=sim_maxiter)
    print(f"VQF (simulator) result: {vqf_dims_sim}")

    if not use_hardware:
        return vqf_dims_sim, vqf_cost_history_sim, None, None

    backend = select_backend(min_num_qubits=1)  # VQF's Hamiltonian qubit count is data-dependent
    print(f"Factoring actual N = {N} with VQF on real hardware ({backend.name})...")
    vqf_dims_hw, vqf_cost_history_hw = run_vqf(
        N, backend=backend, reps=1, maxiter=hw_maxiter, shots=hw_shots
    )
    print(f"VQF (hardware) result: {vqf_dims_hw}")
    return vqf_dims_sim, vqf_cost_history_sim, vqf_dims_hw, vqf_cost_history_hw


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--N", type=int, default=None, help="N to factor")
    parser.add_argument("--hardware", action="store_true", help="Also run on real IBM hardware")
    parser.add_argument("--sim-maxiter", type=int, default=150)
    parser.add_argument("--hw-maxiter", type=int, default=20)
    parser.add_argument("--hw-shots", type=int, default=4096)
    args = parser.parse_args()

    N = args.N
    if N is None:
        from scripts.run_classical_pipeline import run_classical_pipeline
        _, N, _, _ = run_classical_pipeline()

    run_vqf_demo(
        N,
        use_hardware=args.hardware,
        sim_maxiter=args.sim_maxiter,
        hw_maxiter=args.hw_maxiter,
        hw_shots=args.hw_shots,
    )
