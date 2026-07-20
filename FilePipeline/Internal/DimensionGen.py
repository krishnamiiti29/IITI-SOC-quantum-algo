#External Imports
import random

def CreateDimension(N):
	w,h = 0,0
	DimList = []
	for i in range(N):
		width = i
		height = N / i
		if((N % width == 0) & width <= height):
			DimList.append([width, N // i])
	Dimension = random.choice(DimList)
	return Dimension