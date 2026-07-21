import sys
import os
import io



# 1. FIX: Configure the console stream to safely support UTF-8 characters globally once
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Finds 'IITI-SOC-quantum-algo' and adds it to the search path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# External Imports
from FilePipeline.Customize import *
from FilePipeline.Phases.Phase1 import *
from FilePipeline.Phases.Phase2 import *

# Initialisation
N = GiveN()
print(f"Target Number N: {N}")

# Phase 1
MAX_ATTEMPTS = 10
factors_discovered = None

for attempt in range(MAX_ATTEMPTS):
    print(f"\n--- [Phase 1] Shor's Execution Attempt {attempt + 1}/{MAX_ATTEMPTS} ---")
    
    try:
        factors_discovered = ApplyPhase1(N)
        
        if factors_discovered is not None:
            print(f"\n🎉 Success! Found non-trivial factors for {N}: {factors_discovered}")
            break
            
    except ValueError as e:
        print(f" Skipping this attempt: {e}")
        continue
else:
    print(f"\n Failed to isolate factors across {MAX_ATTEMPTS} attempts.")

Width, Height = factors_discovered

# Phase 2

Space = ApplyPhase2(Width, Height)


