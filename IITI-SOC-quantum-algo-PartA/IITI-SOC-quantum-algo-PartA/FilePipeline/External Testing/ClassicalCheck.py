def find_order_classically(a, N):
    """
    Classical reference implementation.

    Finds the smallest positive r such that:

        a^r = 1 mod N

    This is ONLY for verification.
    """

    value = 1

    for r in range(1, N + 1):

        value = (value * a) % N

        if value == 1:
            return r

    return None