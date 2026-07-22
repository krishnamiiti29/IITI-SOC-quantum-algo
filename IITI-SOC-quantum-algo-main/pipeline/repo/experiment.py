"""
experiment.py

Runs the full Shor + Grover pipeline (runner.py) 10 times sequentially,
stores every result to results/run_<i>.json and a combined summary to
results/all_runs.json.

Run with:
    python experiment.py

Then visualise with:
    python plot.py
"""

import json
import os
import traceback
from datetime import datetime

from runner import main as run_once

NUM_EXPERIMENTS = 10
RESULTS_DIR = "results"


def serialise(obj):
    """JSON-safe conversion for numpy types that json.dumps can't handle."""
    import numpy as np
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    raise TypeError(f"Not serialisable: {type(obj)}")


def run_experiment():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    all_runs = []

    for i in range(1, NUM_EXPERIMENTS + 1):
        print(f"\n{'='*60}")
        print(f"  EXPERIMENT RUN {i} / {NUM_EXPERIMENTS}")
        print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

        try:
            result = run_once()
            result["run_index"] = i
            result["status"] = "success"
            result["timestamp"] = datetime.now().isoformat()
        except Exception as e:
            print(f"[ERROR] Run {i} failed: {e}")
            traceback.print_exc()
            result = {
                "run_index": i,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

        # Save individual run
        run_path = os.path.join(RESULTS_DIR, f"run_{i:02d}.json")
        with open(run_path, "w") as f:
            json.dump(result, f, indent=2, default=serialise)
        print(f"\n[Saved] {run_path}")

        all_runs.append(result)

    # Save combined summary
    summary_path = os.path.join(RESULTS_DIR, "all_runs.json")
    with open(summary_path, "w") as f:
        json.dump(all_runs, f, indent=2, default=serialise)
    print(f"\n[Saved] Combined summary -> {summary_path}")

    # Print quick terminal summary
    print(f"\n{'='*60}")
    print("  EXPERIMENT SUMMARY")
    print(f"{'='*60}")
    for r in all_runs:
        if r["status"] == "failed":
            print(f"  Run {r['run_index']:2d}: FAILED  -- {r.get('error','')[:60]}")
        else:
            zne = r.get("zne_estimate", float("nan"))
            key = r.get("key", "?")
            N   = r.get("N", "?")
            print(f"  Run {r['run_index']:2d}: N={N:3}  key={key}  ZNE P(target)={zne:.4f}  "
                  f"{'FOUND' if zne >= 0.5 else 'noisy'}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run_experiment()
