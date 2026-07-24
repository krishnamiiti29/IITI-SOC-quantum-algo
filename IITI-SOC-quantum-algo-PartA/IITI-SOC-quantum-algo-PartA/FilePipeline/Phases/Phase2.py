import sys
import numpy as np

from FilePipeline.Phases.Phase_2.EvenSuperposition import CreateEvenSuperposition
from FilePipeline.Phases.Phase_2.Oracle import BuildGroverCircuit
from FilePipeline.Phases.Phase_2.Mitigation import RunWithMitigation
from FilePipeline.Internal.GenerateKey import GenerateKey
from FilePipeline.Internal.GetHammingWeight import GiveHammingWeight
from FilePipeline.Customize import IBM_API_KEY, IBM_INSTANCE_CRN

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

    # Convert factor values to qubit counts.
    # Width=3, Height=19 are the actual factors from Phase 1.
    # The oracle loops over range(2**width_qubits) and range(2**height_qubits)
    # so passing Width=3 directly would give range(2**3)=8 for x but
    # range(2**19)=524288 for y -- 2 million iterations, hangs forever.
    # Qubit counts: ceil(log2(value+1)) gives the minimum bits to represent
    # all values 0..value, keeping loop sizes small (64 pairs for [3,19]).
    width_qubits  = int(np.ceil(np.log2(Width  + 1)))
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

    # EvenSuperposition takes actual qubit counts, not factor values
    Space = CreateEvenSuperposition(width_qubits, height_qubits)

    # Oracle takes qubit counts -- loops over range(2**width_qubits) etc.
    Space = BuildGroverCircuit(Space, width_qubits, height_qubits, target_parity,
                               iterations=GROVER_ITERATIONS)

    print(f"  Circuit: {Space.num_qubits} qubits, depth={Space.depth()}, "
          f"{GROVER_ITERATIONS} iterations")
    sys.stdout.flush()

    backend = _get_backend()

    zne_estimate, target_probs, raw_counts_by_scale = RunWithMitigation(
        GroverCircuit=Space,
        backend=backend,
        key=Key,
        width=width_qubits,
        height=height_qubits,
        scale_factors=(1, 3, 5),
        shots=4096,
    )

    found = zne_estimate >= 0.5
    print(f"\n  Target key          : {Key}")
    print(f"  P(target) at (1,3,5): {[round(p, 4) for p in target_probs]}")
    print(f"  ZNE P(target)       : {zne_estimate:.4f}")
    print(f"  Result: {'KEY FOUND' if found else 'BEST CANDIDATE (noise present)'}: {Key}")
    sys.stdout.flush()

    return {
        "Space":                 Space,
        "Key":                   Key,
        "Width":                 Width,
        "Height":                Height,
        "width_qubits":          width_qubits,
        "height_qubits":         height_qubits,
        "target_parity":         target_parity,
        "zne_estimate":          zne_estimate,
        "target_probs_by_scale": target_probs,
        "raw_counts_by_scale":   raw_counts_by_scale,
        "scale_factors":         [1, 3, 5],
        "found":                 found,
    }