"""
Phase 1 (classical): prepare the search space for a random N, then use
classical statevector-based order finding to recover a nontrivial factor
pair (Width, Height) of N.

Mirrors the notebook's cells 0-3 ("Import Block" through the Width/Height
resolution cell).

Usage:
    python scripts/run_classical_pipeline.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from qc_pipeline.space_prep.initiate import Initiate
from qc_pipeline.space_prep.classical_order_finding import ProvideDimensions


def run_classical_pipeline():
    Space, N = Initiate()

    dims = None
    while dims is None:
        dims = ProvideDimensions(N)
    Dim1, Dim2 = dims

    if Dim1 <= Dim2:
        Width, Height = Dim1, Dim2
    else:
        Width, Height = Dim2, Dim1

    print(f"Width is: {Width}, and Height is: {Height}")
    return Space, N, Width, Height


if __name__ == "__main__":
    run_classical_pipeline()
