"""
End-to-end quantum factoring pipeline (simulator-only, no IBM hardware
account required).

Runs:
  Phase 1: pick a random N, prepare quantum registers, classically recover
           a nontrivial factor pair (Width, Height) of N.
  Phase 2/3: build a constrained even superposition over the search space,
             apply a Hamming-weight resonance oracle + pi/3 diffuser to
             amplify a randomly chosen target key, simulate, and report the
             top measured (x, y) pairs.

For the alternative QPE / VQF order-finding approaches and the real-IBM-
hardware / error-mitigated variants, see the standalone scripts in scripts/.

Usage:
    python main.py
"""

from scripts.run_classical_pipeline import run_classical_pipeline
from scripts.run_grover_pipeline import run_grover_pipeline


def main():
    print("=== Phase 1: classical space preparation + order finding ===")
    Space, N, Width, Height = run_classical_pipeline()

    print("\n=== Phase 2/3: Grover build, oracle, diffuser, simulate ===")
    OracleSpace, key, decoded_counts, width_qubits, height_qubits, search_qubits_count = (
        run_grover_pipeline(Space, N, Width, Height)
    )

    return {
        "N": N,
        "Width": Width,
        "Height": Height,
        "key": key,
        "decoded_counts": decoded_counts,
        "OracleSpace": OracleSpace,
        "width_qubits": width_qubits,
        "height_qubits": height_qubits,
        "search_qubits_count": search_qubits_count,
    }


if __name__ == "__main__":
    main()
