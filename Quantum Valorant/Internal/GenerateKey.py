import random

from Internal.GetHammingWeight import GiveHammingWeight


def GenerateKey(Dimension):
    x, y = Dimension
    KeyList = []

    TargetWeightSum = GiveHammingWeight(x) + GiveHammingWeight(y)

    for i in range(0, x, 2):  # even x values only, my lord and saviour, the PS, asks for this, for some reason
        weight_i = GiveHammingWeight(i)
        for j in range(y):
            if (weight_i ^ GiveHammingWeight(j)) == TargetWeightSum:
                KeyList.append([i, j])

    if KeyList:
        return random.choice(KeyList)

    return None