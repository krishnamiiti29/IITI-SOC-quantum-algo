from Internal.GenerateKey import GenerateKey
from Internal.SpaceGen import CreateSpace


def Initiate(N):
    Space, Dimensions = CreateSpace(N)
    Key = GenerateKey(Dimensions)
    return Space, Dimensions, Key