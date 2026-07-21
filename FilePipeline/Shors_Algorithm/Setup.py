import math
import random


def ChooseGamma(N):
	GammaList = []
	for i in range(N):
		if ((i > 1) & math.gcd(i, N) == 1):
			GammaList.append(i)
	Gamma = random.choice(GammaList)
	return Gamma