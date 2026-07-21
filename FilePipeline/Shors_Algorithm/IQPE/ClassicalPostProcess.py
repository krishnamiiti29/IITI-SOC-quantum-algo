from FilePipeline.Shors_Algorithm.IQPE.OrderRecovery import *


def bitstring_to_phase(bitstring):
    """
    Convert a binary phase estimate into a number in [0, 1).
    """

    return int(bitstring, 2) / (2 ** len(bitstring))

def estimate_order_from_counts(counts, a, N):
    """
    Try each measured phase value and recover an order.
    """

    for bitstring, count in sorted(
        counts.items(),
        key=lambda x: x[1],
        reverse=True
    ):

        phase = bitstring_to_phase(bitstring)

        print(
            f"Measurement: {bitstring}"
        )

        print(
            f"Estimated phase: {phase}"
        )

        candidate_r = continued_fraction_order(
            phase,
            a,
            N
        )

        if candidate_r is not None:

            print(
                f"Candidate order r = {candidate_r}"
            )

            return candidate_r

    return None