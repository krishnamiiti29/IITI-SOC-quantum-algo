def GiveHammingWeight(x):
    BitX = bin(x)[2:]
    return BitX.count("1")