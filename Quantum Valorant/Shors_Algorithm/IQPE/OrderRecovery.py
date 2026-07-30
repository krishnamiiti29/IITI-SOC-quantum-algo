from fractions import Fraction


def continued_fraction_order(phase, a, N):
    """
    Given an estimated phase ≈ s / r, recover the order r using continued
    fractions. The candidate denominator is verified via a^r mod N == 1.
    """
    fraction = Fraction(phase).limit_denominator(N)
    candidate_r = fraction.denominator

    if pow(a, candidate_r, N) == 1:
        return candidate_r

    return None