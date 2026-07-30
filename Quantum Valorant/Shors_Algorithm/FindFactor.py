import math


def recover_factors(a, N, r):
    if r is None:
        return None

    if r % 2 != 0:
        return None

    x = pow(a, r // 2, N)

    if x == N - 1:
        return None

    factor_1 = math.gcd(x - 1, N)
    factor_2 = math.gcd(x + 1, N)

    if factor_1 == 1 or factor_1 == N:
        return None

    if factor_2 == 1 or factor_2 == N:
        return None

    if factor_1 < factor_2:
        tempfactor = factor_2
        factor_2 = factor_1
        factor_1 = factor_2

    factor_2 = N // factor_1

    return factor_1, factor_2