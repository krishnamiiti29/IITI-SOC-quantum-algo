#External Imports
import random
#Internal Connections
from FilePipeline.Internal.GetHammingWeight import GiveHammingWeight

def GenerateKey(Dimension):
	x,y = Dimension
	KeyList = []
	for i in range(x):
		if (i % 2 == 0):
			for j in range(y):
				if((GiveHammingWeight(i) ^ GiveHammingWeight(j)) == (GiveHammingWeight(x) + GiveHammingWeight(y))):
					KeyList.append([i,j])
	if (len(KeyList) > 0):
		Key = random.choice(KeyList)
		return Key
	else:
		return None
