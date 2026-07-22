#External Imports
import random

# Internal Connections
from FilePipeline.Internal.GetHammingWeight import GiveHammingWeight


def GenerateKey(Dimension):
    x, y = Dimension
    KeyList = []

    # Calculate this ONCE outside the loop to save massive CPU cycles
    TargetWeightSum = GiveHammingWeight(x) + GiveHammingWeight(y)

    # range(0, x, 2) automatically selects only even numbers, skipping the 'if' check
    for i in range(0, x, 2):
        weight_i = GiveHammingWeight(i)

        for j in range(y):
            # Check the XOR condition
            if (weight_i ^ GiveHammingWeight(j)) == TargetWeightSum:
                KeyList.append([i, j])

    # Clean, Pythonic check for an empty list
    if KeyList:
        return random.choice(KeyList)

    return None

