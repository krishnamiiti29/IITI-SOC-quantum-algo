#External Imports
import random


def CreateDimension(N):
    DimList = []

    for i in range(2, int(N**0.5) + 1):
        if N % i == 0:
            DimList.append([i, N // i])

    if not DimList:
        return None

    return random.choice(DimList)