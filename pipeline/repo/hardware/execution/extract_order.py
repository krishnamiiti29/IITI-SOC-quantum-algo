from fractions import Fraction
import math


def extract_order_from_counts(counts, t_phase, N, gamma):
    per_shot = {}
    valid_candidates = []

    for bitstring, _count in counts.items():
        measured_int = int(bitstring, 2)
        phi = measured_int / (2 ** t_phase)

        if phi == 0:
            per_shot[bitstring] = None
            continue

        frac = Fraction(phi).limit_denominator(N - 1)
        r_candidate = frac.denominator

        if r_candidate > 0 and pow(gamma, r_candidate, N) == 1:
            per_shot[bitstring] = r_candidate
            valid_candidates.append(r_candidate)
        else:
            per_shot[bitstring] = None

    combined_r = None
    for r in valid_candidates:
        combined_r = r if combined_r is None else math.lcm(combined_r, r)
        if pow(gamma, combined_r, N) != 1:
            combined_r = max(valid_candidates)
            break

    return combined_r
