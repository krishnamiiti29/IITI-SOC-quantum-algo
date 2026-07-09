"""
Plotting helpers: full measured (x, y) distributions, QAOA cost
convergence, and the Grover ZNE extrapolation fit.

Extracted from the notebook's plotting cells.
"""

import numpy as np
import matplotlib.pyplot as plt

from qc_pipeline.hardware.mitigation import zne_extrapolate


def plot_full_distribution(decoded_counts, target_key, title):
    """Bar-plot the full measured (x, y) distribution, highlighting the target key in red."""
    sorted_items = sorted(decoded_counts.items(), key=lambda kv: -kv[1])
    labels = [str(xy) for xy, _ in sorted_items]
    values = [count for _, count in sorted_items]
    colors = ["crimson" if list(xy) == target_key else "steelblue" for xy, _ in sorted_items]

    plt.figure(figsize=(max(10, len(labels) * 0.3), 5))
    plt.bar(range(len(labels)), values, color=colors)
    plt.xticks(range(len(labels)), labels, rotation=90, fontsize=7)
    plt.xlabel("(x, y)")
    plt.ylabel("Shots")
    plt.title(f"{title}  (red = target key {target_key})")
    plt.tight_layout()
    plt.show()


def plot_qaoa_convergence(cost_history, title="QAOA cost convergence"):
    """Line-plot the QAOA cost (Hamiltonian expectation) per COBYLA iteration."""
    plt.figure(figsize=(8, 4))
    plt.plot(cost_history, marker="o", markersize=3)
    plt.xlabel("Iteration")
    plt.ylabel("Cost (Hamiltonian expectation)")
    plt.title(title)
    plt.tight_layout()
    plt.show()


def plot_zne_fit(scale_factors, target_probs, title="ZNE fit"):
    """Scatter the folded measurements and overlay the linear ZNE extrapolation fit."""
    zne_estimate, coeffs = zne_extrapolate(scale_factors, target_probs, order=1)
    xs = np.linspace(0, max(scale_factors), 50)
    ys = np.polyval(coeffs, xs)
    plt.figure(figsize=(6, 4))
    plt.scatter(scale_factors, target_probs, color="steelblue", label="Measured (folded)")
    plt.plot(xs, ys, color="crimson", linestyle="--", label="Linear fit")
    plt.scatter(
        [0], [zne_estimate], color="crimson", zorder=5,
        label=f"Zero-noise estimate = {zne_estimate:.4f}",
    )
    plt.xlabel("Noise scale factor")
    plt.ylabel("P(target key)")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.show()
