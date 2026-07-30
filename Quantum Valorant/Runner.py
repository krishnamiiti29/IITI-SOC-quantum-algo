import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True, write_through=True)

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from FilePipeline.Customize import *
from FilePipeline.Phases.Phase1 import *
from FilePipeline.Phases.Phase2 import *
from FilePipeline.Internal.DimensionGen import *
from FilePipeline.Internal.GenerateKey import *

N = GiveN()
print(f"Target Number N: {N}")
Dimensions = CreateDimension(N)
print(f"Target Dimension: {Dimensions}")
Key = GenerateKey(Dimensions)
print(f"Target Key: {Key}")

# Phase 1
MAX_ATTEMPTS = 20
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