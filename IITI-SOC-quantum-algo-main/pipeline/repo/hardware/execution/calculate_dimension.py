import math

def calculate_dimensions_from_order(r, gamma, N):
    if r is None or r % 2 != 0:
        return None, None

    x = pow(int(gamma), r // 2, int(N))
    if (x + 1) % N == 0:
        return None, None

    factor1 = math.gcd(N, int(x + 1))
    factor2 = N // factor1

    return sorted([int(factor1), int(factor2)])
