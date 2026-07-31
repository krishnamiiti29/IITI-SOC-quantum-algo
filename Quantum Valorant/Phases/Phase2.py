import sys
import os
import numpy as np

from Phases.Phase_2.EvenSuperposition import CreateEvenSuperposition
from Phases.Phase_2.Oracle import BuildGroverCircuit
from Phases.Phase_2.Mitigation import RunWithMitigation
from Internal.GenerateKey import GenerateKey
from Internal.GetHammingWeight import GiveHammingWeight
from Customize import IBM_API_KEY, IBM_INSTANCE_CRN

from qiskit import ClassicalRegister, transpile
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import QiskitRuntimeService

GROVER_ITERATIONS = 8


def _get_backend():
    kwargs = {"channel": "ibm_quantum_platform", "token": IBM_API_KEY}
    if IBM_INSTANCE_CRN:
        kwargs["instance"] = IBM_INSTANCE_CRN
    service = QiskitRuntimeService(**kwargs)
    backend = service.least_busy(operational=True, simulator=False, min_num_qubits=10)
    print(f"  Using backend: {backend.name} ({backend.num_qubits} qubits)")
    sys.stdout.flush()
    return backend


def ApplyPhase2(Width, Height):
    print("\n--- [Phase 2] Parity-Restricted Grover Search ---")
    sys.stdout.flush()

    width_qubits = int(np.ceil(np.log2(Width + 1)))
    height_qubits = int(np.ceil(np.log2(Height + 1)))
    print(f"  Width={Width} ({width_qubits} qubits)  Height={Height} ({height_qubits} qubits)")
    sys.stdout.flush()

    Key = GenerateKey([Width, Height])
    if Key is None:
        print("  [WARNING] GenerateKey returned None -- no valid key for these dimensions.")
        sys.stdout.flush()
        return None

    print(f"  Key={Key}")
    sys.stdout.flush()

    target_parity = (GiveHammingWeight(Width) + GiveHammingWeight(Height)) % 2
    print(f"  Target parity: {target_parity}")
    sys.stdout.flush()

    Space = CreateEvenSuperposition(width_qubits, height_qubits)
    Space = BuildGroverCircuit(Space, width_qubits, height_qubits, target_parity,
                               iterations=GROVER_ITERATIONS)

    print(f"  Circuit: {Space.num_qubits} qubits, depth={Space.depth()}, "
          f"{GROVER_ITERATIONS} iterations")
    sys.stdout.flush()

    # Noiseless simulator: measure directly, mitigation stack skipped
    search_qubits = list(range(width_qubits + height_qubits))
    creg = ClassicalRegister(len(search_qubits), name="result")
    Space.add_register(creg)
    Space.measure(search_qubits, creg)

    backend = _get_backend()
    transpiled_circuit = transpile(Space, backend=backend)

    job = backend.run(transpiled_circuit, shots=4096)
    counts = job.result().get_counts()

    heatmap_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phase2_heatmap.png")

    fig, probability_grid, leaked_p = PlotHeatmap(
        counts, width_qubits, height_qubits, Width, Height, key=Key,
        title=f"P(x, y) preparation -- Width={Width}, Height={Height}",
        save_path=heatmap_path,
    )

    p_target = probability_grid[Key[0], Key[1]]
    found = p_target >= 0.5

    print(f"\n  Target key   : {Key}")
    print(f"  P(target)    : {p_target:.4f}")
    print(f"  Result: {'KEY FOUND' if found else 'BEST CANDIDATE'}: {Key}")
    sys.stdout.flush()

    return {
        "Space": Space,
        "Key": Key,
        "Width": Width,
        "Height": Height,
        "width_qubits": width_qubits,
        "height_qubits": height_qubits,
        "target_parity": target_parity,
        "counts": counts,
        "probability_grid": probability_grid,
        "leaked_probability": leaked_p,
        "p_target": p_target,
        "found": found,
        "heatmap_fig": fig,
    }