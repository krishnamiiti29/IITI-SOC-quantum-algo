#External Imports
import random


def CreateDimension(N):
    DimList = []
    
    # Loop from 1 up to the square root of N (inclusive)
    for i in range(2, int(N**0.5) + 1):
        # Check if i is a clean factor of N
        if (N % i == 0):
            width = i
            height = N // i
            DimList.append([width, height])
            
    # Safeguard against N <= 0 or empty lists
    if not DimList:
        return None
        
    return random.choice(DimList)
