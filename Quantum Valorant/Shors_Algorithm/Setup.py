import math
import random


def ChooseGamma(N):
    GammaList = [i for i in range(N) if i > 1 and math.gcd(i, N) == 1]
    return random.choice(GammaList)