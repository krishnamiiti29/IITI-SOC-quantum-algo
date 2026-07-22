"""
plot.py

Reads results/all_runs.json produced by experiment.py and generates four
sets of plots, saved to results/plots/:

  1. top10_run_<i>.png  -- bar chart of top-10 measured (x,y) pairs for
                           each of the 10 runs (scale factor = 1, raw counts)

  2. target_shots.png   -- line + scatter: raw shots landing on the target
                           key across all 10 runs (scale=1 counts)

  3. zne_curves.png     -- one subplot per run: P(target) vs noise scale
                           (1, 3, 5) with ZNE extrapolation line to scale=0

  4. summary.png        -- grouped bar chart comparing ZNE estimate vs
                           raw (scale=1) P(target) across all 10 runs

Run with:
    python plot.py
"""

import json
import os
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

RESULTS_PATH = os.path.join("results", "all_runs.json")
PLOTS_DIR    = os.path.join("results", "plots")
SCALE_FACTORS = [1, 3, 5]


# ── helpers ────────────────────────────────────────────────────────────────

def load_runs():
    with open(RESULTS_PATH) as f:
        return json.load(f)


def decode_counts(raw_counts, width_qubits, height_qubits):
    """Convert raw bitstring->count dict into (x,y)->count dict."""
    decoded = {}
    for bitstring, count in raw_counts.items():
        bits = bitstring[::-1]
        x_bits = bits[0:width_qubits]
        y_bits = bits[width_qubits:width_qubits + height_qubits]
        x_val  = int(x_bits[::-1], 2)
        y_val  = int(y_bits[::-1], 2)
        xy = (x_val, y_val)
        decoded[xy] = decoded.get(xy, 0) + count
    return decoded


def key_to_bitstring(key, width_qubits, height_qubits):
    x_bits = format(key[0], f"0{width_qubits}b")[::-1]
    y_bits = format(key[1], f"0{height_qubits}b")[::-1]
    return (x_bits + y_bits)[::-1]


def style():
    plt.rcParams.update({
        "figure.facecolor":  "#0f0f1a",
        "axes.facecolor":    "#1a1a2e",
        "axes.edgecolor":    "#444466",
        "axes.labelcolor":   "#ccccee",
        "axes.titlecolor":   "#ffffff",
        "xtick.color":       "#aaaacc",
        "ytick.color":       "#aaaacc",
        "text.color":        "#ccccee",
        "grid.color":        "#2a2a4a",
        "grid.linestyle":    "--",
        "grid.alpha":        0.5,
        "legend.facecolor":  "#1a1a2e",
        "legend.edgecolor":  "#444466",
        "font.family":       "monospace",
    })


# ── Plot 1: top-10 bar charts (one per run) ────────────────────────────────

def plot_top10(runs):
    for r in runs:
        if r["status"] != "success":
            continue

        i            = r["run_index"]
        key          = tuple(r["key"])
        wq           = r["width_qubits"]
        hq           = r["height_qubits"]
        raw_counts   = r["raw_counts_by_scale"][0]   # scale factor = 1
        decoded      = decode_counts(raw_counts, wq, hq)
        top10        = sorted(decoded.items(), key=lambda kv: -kv[1])[:10]

        labels  = [str(xy) for xy, _ in top10]
        values  = [c for _, c in top10]
        colours = ["#ff4444" if xy == key else "#4488ff" for xy, _ in top10]

        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.bar(labels, values, color=colours, edgecolor="#222244", linewidth=0.8)
        ax.set_title(f"Run {i:02d}  |  N={r['N']}  key={list(key)}  "
                     f"target_parity={r['target_parity']}",
                     fontsize=12, pad=12)
        ax.set_xlabel("(x, y)")
        ax.set_ylabel("Shots")
        ax.yaxis.grid(True)
        ax.set_axisbelow(True)

        # annotate each bar with its count
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.01,
                    str(val), ha="center", va="bottom", fontsize=8, color="#ccccee")

        # legend
        from matplotlib.patches import Patch
        ax.legend(handles=[Patch(color="#ff4444", label="Target key"),
                            Patch(color="#4488ff", label="Other states")],
                  loc="upper right")

        out = os.path.join(PLOTS_DIR, f"top10_run_{i:02d}.png")
        fig.tight_layout()
        fig.savefig(out, dpi=150)
        plt.close(fig)
        print(f"[Saved] {out}")


# ── Plot 2: shots on target key across all runs ────────────────────────────

def plot_target_shots(runs):
    run_indices   = []
    target_shots  = []
    total_shots   = []

    for r in runs:
        if r["status"] != "success":
            continue
        key   = r["key"]
        wq    = r["width_qubits"]
        hq    = r["height_qubits"]
        tbstr = key_to_bitstring(key, wq, hq)
        raw   = r["raw_counts_by_scale"][0]   # scale=1
        run_indices.append(r["run_index"])
        target_shots.append(raw.get(tbstr, 0))
        total_shots.append(sum(raw.values()))

    target_pct = [100 * t / tot for t, tot in zip(target_shots, total_shots)]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    # raw counts
    ax1.plot(run_indices, target_shots, "o-", color="#ff4444", linewidth=2,
             markersize=8, markeredgecolor="#ffffff", markeredgewidth=0.8)
    ax1.fill_between(run_indices, target_shots, alpha=0.15, color="#ff4444")
    ax1.set_ylabel("Raw shots on target key")
    ax1.set_title("Shots landing on target key across 10 runs  (scale factor = 1)", pad=10)
    ax1.yaxis.grid(True)
    ax1.set_axisbelow(True)
    for xi, yi in zip(run_indices, target_shots):
        ax1.annotate(str(yi), (xi, yi), textcoords="offset points",
                     xytext=(0, 8), ha="center", fontsize=8)

    # percentage
    ax2.bar(run_indices, target_pct, color="#44bbff", edgecolor="#222244", linewidth=0.8)
    ax2.axhline(100 / (2 ** (run_indices[0] if run_indices else 1)),
                color="#888888", linestyle="--", linewidth=1, label="Uniform random baseline")
    ax2.set_xlabel("Run index")
    ax2.set_ylabel("% of total shots")
    ax2.set_title("Target key as % of total shots", pad=10)
    ax2.yaxis.grid(True)
    ax2.set_axisbelow(True)
    ax2.legend()
    ax2.set_xticks(run_indices)

    out = os.path.join(PLOTS_DIR, "target_shots.png")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"[Saved] {out}")


# ── Plot 3: ZNE mitigation curves (one subplot per run) ───────────────────

def plot_zne_curves(runs):
    successful = [r for r in runs if r["status"] == "success"]
    n = len(successful)
    if n == 0:
        return

    cols = min(5, n)
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 4, rows * 3.5))
    axes = np.array(axes).flatten()

    for ax, r in zip(axes, successful):
        probs  = r["target_probs_by_scale"]    # P(target) at scale 1,3,5
        scales = r["scale_factors"]
        zne    = r["zne_estimate"]

        # fit line through the three points
        coeffs   = np.polyfit(scales, probs, 1)
        xs_extrap = np.linspace(0, max(scales), 100)
        ys_extrap = np.polyval(coeffs, xs_extrap)

        ax.plot(xs_extrap, ys_extrap, "--", color="#888888", linewidth=1.2,
                label="ZNE fit")
        ax.scatter(scales, probs, color="#ff8844", s=80, zorder=5,
                   edgecolors="#ffffff", linewidths=0.8, label="Measured")
        ax.scatter([0], [zne], color="#44ff88", s=120, zorder=6,
                   marker="*", edgecolors="#ffffff", linewidths=0.8,
                   label=f"ZNE={zne:.3f}")
        ax.axvline(0, color="#444466", linewidth=0.8, linestyle=":")
        ax.set_xlim(-0.3, max(scales) + 0.3)
        ax.set_title(f"Run {r['run_index']:02d}  N={r['N']}  key={r['key']}", fontsize=9)
        ax.set_xlabel("Noise scale factor")
        ax.set_ylabel("P(target)")
        ax.yaxis.grid(True)
        ax.set_axisbelow(True)
        ax.legend(fontsize=7)

    # hide unused subplots
    for ax in axes[n:]:
        ax.set_visible(False)

    fig.suptitle("ZNE Mitigation Curves — P(target key) vs Noise Scale", fontsize=13, y=1.01)
    out = os.path.join(PLOTS_DIR, "zne_curves.png")
    fig.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[Saved] {out}")


# ── Plot 4: summary — ZNE vs raw P(target) across all runs ────────────────

def plot_summary(runs):
    successful = [r for r in runs if r["status"] == "success"]
    if not successful:
        return

    indices    = [r["run_index"] for r in successful]
    zne_vals   = [r["zne_estimate"] for r in successful]
    raw_vals   = [r["target_probs_by_scale"][0] for r in successful]  # scale=1

    x     = np.arange(len(indices))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 5))
    b1 = ax.bar(x - width/2, raw_vals, width, label="Raw P(target)  scale=1",
                color="#4488ff", edgecolor="#222244")
    b2 = ax.bar(x + width/2, zne_vals, width, label="ZNE P(target)  extrapolated",
                color="#44ff88", edgecolor="#222244")

    ax.axhline(0.5, color="#ffcc44", linestyle="--", linewidth=1.2,
               label="P=0.5 decision threshold")
    ax.set_xticks(x)
    ax.set_xticklabels([f"Run {i}\nN={r['N']}" for i, r in
                        zip(indices, successful)], fontsize=8)
    ax.set_ylabel("P(target key found)")
    ax.set_title("Error Mitigation Effect: Raw vs ZNE P(target) across all runs", pad=12)
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)
    ax.legend()

    # annotate bars
    for bar in b1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.005,
                f"{h:.3f}", ha="center", va="bottom", fontsize=7)
    for bar in b2:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.005,
                f"{h:.3f}", ha="center", va="bottom", fontsize=7)

    out = os.path.join(PLOTS_DIR, "summary.png")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"[Saved] {out}")


# ── main ───────────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(RESULTS_PATH):
        print(f"[ERROR] {RESULTS_PATH} not found. Run experiment.py first.")
        return

    os.makedirs(PLOTS_DIR, exist_ok=True)
    style()

    runs = load_runs()
    print(f"Loaded {len(runs)} runs from {RESULTS_PATH}")

    print("\n[1/4] Plotting top-10 bar charts per run...")
    plot_top10(runs)

    print("\n[2/4] Plotting target key shots across runs...")
    plot_target_shots(runs)

    print("\n[3/4] Plotting ZNE mitigation curves...")
    plot_zne_curves(runs)

    print("\n[4/4] Plotting summary comparison...")
    plot_summary(runs)

    print(f"\nAll plots saved to {PLOTS_DIR}/")


if __name__ == "__main__":
    main()
