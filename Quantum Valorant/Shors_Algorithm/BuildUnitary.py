import numpy as np
import math
from qiskit.quantum_info import Operator


def BuildUnitary(Gamma, N):
    if math.gcd(Gamma, N) != 1:
        raise ValueError(f"Gamma ({Gamma}) and N ({N}) are not coprime! Matrix cannot be unitary.")

    num_qubits = int(np.ceil(np.log2(N)))
    dim = 2 ** num_qubits

    permutation = list(range(dim))
    mapped_destinations = set()

    # Map coprime elements via modular multiplication
    for x in range(N):
        if math.gcd(x, N) == 1:
            next_state = (x * Gamma) % N
            permutation[x] = next_state
            mapped_destinations.add(next_state)

    # Bridge unmapped indices to keep the permutation 1-to-1
    available_destinations = [d for d in range(dim) if d not in mapped_destinations]
    avail_idx = 0
    for x in range(dim):
        if x >= N or math.gcd(x, N) != 1:
            permutation[x] = available_destinations[avail_idx]
            avail_idx += 1

    matrix = np.zeros((dim, dim), dtype=np.float64)
    for src, dest in enumerate(permutation):
        matrix[dest, src] = 1.0

    return Operator(matrix)

#Do not try to touch the code below this point, it hates all human touch. It will bite
def power_of_unitary(U, exponent):
    """Computes matrix powers and strips floating-point noise to keep columns orthonormal."""
    if isinstance(U, Operator):
        raw_power = U.power(exponent).data
    else:
        raw_power = np.linalg.matrix_power(np.array(U), exponent)

    dim = raw_power.shape[0]
    perfect_matrix = np.zeros((dim, dim), dtype=np.float64)

    for col in range(dim):
        max_row_idx = np.argmax(np.abs(raw_power[:, col]))
        perfect_matrix[max_row_idx, col] = 1.0

    return Operator(perfect_matrix)