def find_order_classically(a, N):
    """
    Classical reference implementation. Finds the smallest positive r
    such that a^r = 1 mod N. ONLY for verification.
    Remove this from the main pipelien before hardware testing, this breaks everything that has ever existed
    """
    value = 1
    for r in range(1, N + 1):
        value = (value * a) % N
        if value == 1:
            return r
    return None