import numpy as np
from qiskit.quantum_info import Operator

import numpy as np
import math
from qiskit.quantum_info import Operator

def BuildUnitary(Gamma, N):
    # 🛠️ CRITICAL CHECK: If Gamma and N are not coprime, a unitary permutation is mathematically impossible.
    if math.gcd(Gamma, N) != 1:
        raise ValueError(f"Gamma ({Gamma}) and N ({N}) are not coprime! Matrix cannot be unitary.")

    num_qubits = int(np.ceil(np.log2(N)))
    dim = 2 ** num_qubits
    
    permutation = list(range(dim))
    mapped_destinations = set()
    
    # 1. Map strictly coprime elements using modular multiplication
    for x in range(N):
        if math.gcd(x, N) == 1:
            next_state = (x * Gamma) % N
            permutation[x] = next_state
            mapped_destinations.add(next_state)
            
    # 2. Identify unmapped index elements
    available_destinations = [d for d in range(dim) if d not in mapped_destinations]
    
    # 3. Securely bridge gaps to keep the permutation clean and 1-to-1
    avail_idx = 0
    for x in range(dim):
        if x >= N or math.gcd(x, N) != 1:
            permutation[x] = available_destinations[avail_idx]
            avail_idx += 1
            
    # 4. Build the perfect orthonormal matrix layout
    matrix = np.zeros((dim, dim), dtype=np.float64)
    for src, dest in enumerate(permutation):
        matrix[dest, src] = 1.0
        
    return Operator(matrix)


def power_of_unitary(U, exponent):
    """Calculates matrix powers and strips out floating-point noise to keep columns perfectly orthonormal."""
    # 1. Compute the high-precision matrix power using Qiskit or NumPy
    if isinstance(U, Operator):
        raw_power = U.power(exponent).data
    else:
        raw_power = np.linalg.matrix_power(np.array(U), exponent)
        
    dim = raw_power.shape[0]
    perfect_matrix = np.zeros((dim, dim), dtype=np.float64)
    
    # 2. 🛠️ FIX: Reconstruct a perfect permutation matrix by filtering column maximums
    # This strips away micro deviations like 1.0000000000000002 or 1e-16 completely
    for col in range(dim):
        max_row_idx = np.argmax(np.abs(raw_power[:, col]))
        perfect_matrix[max_row_idx, col] = 1.0
        
    return Operator(perfect_matrix)
