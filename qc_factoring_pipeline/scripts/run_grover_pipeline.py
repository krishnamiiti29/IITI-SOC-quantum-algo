"""
Phase 2/3: build the constrained even superposition, apply the Hamming-weight
resonance oracle + pi/3 diffuser to amplify the target key, then simulate
and decode the measured (x, y) results.

Mirrors the notebook's cells 14-15. Runs the classical Phase 1 pipeline
first (scripts.run_classical_pipeline) to obtain Space/N/Width/Height,
unless those are passed in directly.

Usage:
    python scripts/run_grover_pipeline.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from qiskit import ClassicalRegister, transpile
from qiskit_aer import AerSimulator

from qc_pipeline.utils.dimension_utils import GiveQubitCount, KeyChoice, GiveHammingWeight
from qc_pipeline.grover.superposition import CreateConstrainedEvenSuperposition
from qc_pipeline.grover.oracle import ApplyHammingWeightResonanceOracle, build_pi3_diffuser
from qc_pipeline.grover.decode import decode_counts


def build_search_circuit(Space, N, Width, Height):
    """Build EvenSpace -> OracleSpace and pick the target key. Mirrors notebook cell 14."""
    width_qubits, height_qubits = GiveQubitCount([Width, Height])
    search_qubits_count = width_qubits + height_qubits

    EvenSpace = CreateConstrainedEvenSuperposition(Space, N, width_qubits)
    print(EvenSpace.draw("text"))

    key = KeyChoice((Width, Height))
    print(f"Key: {key}")
    print(GiveHammingWeight(key[0]) % 2, GiveHammingWeight(key[1]) % 2)

    # Put the oracle's "target" ancilla into |-> for phase kickback.
    EvenSpace.x(search_qubits_count + 2)
    EvenSpace.h(search_qubits_count + 2)

    OracleSpace = ApplyHammingWeightResonanceOracle(EvenSpace, width_qubits, search_qubits_count, 1)
    diffuser = build_pi3_diffuser(search_qubits_count)
    OracleSpace.append(diffuser, list(range(search_qubits_count)))

    return OracleSpace, key, width_qubits, height_qubits, search_qubits_count


def simulate_and_decode(OracleSpace, key, width_qubits, height_qubits, search_qubits_count, shots=2048):
    """Measure the search qubits and decode the result back into (x, y). Mirrors notebook cell 15."""
    sim_circuit = OracleSpace.copy()
    creg = ClassicalRegister(search_qubits_count, name="result")
    sim_circuit.add_register(creg)
    sim_circuit.measure(list(range(search_qubits_count)), creg)

    simulator = AerSimulator()
    compiled = transpile(sim_circuit, simulator)
    result = simulator.run(compiled, shots=shots).result()
    counts = result.get_counts()

    decoded_counts = decode_counts(counts, width_qubits, height_qubits)
    sorted_results = sorted(decoded_counts.items(), key=lambda kv: -kv[1])

    print(f"Target key: {key}")
    print("Top measured (x, y) pairs:")
    for (x_val, y_val), count in sorted_results[:10]:
        marker = " <-- TARGET" if [x_val, y_val] == key else ""
        print(f"  ({x_val}, {y_val}): {count} shots{marker}")

    return decoded_counts


def run_grover_pipeline(Space=None, N=None, Width=None, Height=None, shots=2048):
    if Space is None or N is None or Width is None or Height is None:
        from scripts.run_classical_pipeline import run_classical_pipeline
        Space, N, Width, Height = run_classical_pipeline()

    OracleSpace, key, width_qubits, height_qubits, search_qubits_count = build_search_circuit(
        Space, N, Width, Height
    )
    decoded_counts = simulate_and_decode(
        OracleSpace, key, width_qubits, height_qubits, search_qubits_count, shots=shots
    )
    return OracleSpace, key, decoded_counts, width_qubits, height_qubits, search_qubits_count


if __name__ == "__main__":
    run_grover_pipeline()
