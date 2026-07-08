import math

def calculate_dimensions_from_order(r, gamma, N):
    """
    Applies Shor's classical factor-finding step to derive the dimensions (factors) of N.
    Returns a tuple of factors (factor1, factor2) if successful, else (None, None).
    """
    if r is None or r % 2 != 0:
        return None, None
    
    x = pow(int(gamma), r // 2, int(N))
    if (x + 1) % N == 0:
        return None, None  # Trivial factors found
        
    factor1 = math.gcd(N, int(x + 1))
    factor2 = N // factor1
    
    # Sort them to keep output consistent (e.g., [3, 7] instead of [7, 3])
    return sorted([int(factor1), int(factor2)])
