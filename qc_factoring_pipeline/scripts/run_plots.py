"""
Plot results from the other pipeline stages: full measured (x, y)
distributions (simulator/hardware), VQF/QAOA cost convergence, and the
Grover ZNE extrapolation fit.

Mirrors the notebook's plotting cells (19 and 22). Call the individual
plotting functions with whatever results you have -- not every result
needs to be present.

Usage (as a library, after running other scripts and collecting results):
    from scripts.run_plots import plot_all
    plot_all(decoded_counts=..., decoded_hw_counts=..., key=key,
             vqf_cost_history_sim=..., vqf_cost_history_hw=...,
             scale_factors=..., target_probs_by_scale=...)
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from qc_pipeline.visualization.plots import (
    plot_full_distribution,
    plot_qaoa_convergence,
    plot_zne_fit,
)


def plot_all(decoded_counts=None, decoded_hw_counts=None, key=None,
             vqf_cost_history_sim=None, vqf_cost_history_hw=None,
             scale_factors=None, target_probs_by_scale=None):
    plotted_any = False

    if decoded_counts is not None:
        plot_full_distribution(decoded_counts, key, "Simulator: full measured distribution")
        plotted_any = True

    if decoded_hw_counts is not None:
        plot_full_distribution(decoded_hw_counts, key, "Hardware: full measured distribution")
        plotted_any = True

    if not plotted_any:
        print(
            "Nothing to plot: pass decoded_counts (simulator) and/or "
            "decoded_hw_counts (hardware)."
        )

    plotted_any_graph = False

    if vqf_cost_history_sim:
        plot_qaoa_convergence(vqf_cost_history_sim, "VQF QAOA convergence (simulator)")
        plotted_any_graph = True

    if vqf_cost_history_hw:
        plot_qaoa_convergence(vqf_cost_history_hw, "VQF QAOA convergence (hardware)")
        plotted_any_graph = True

    if scale_factors is not None and target_probs_by_scale is not None:
        plot_zne_fit(scale_factors, target_probs_by_scale, "Grover ZNE extrapolation")
        plotted_any_graph = True

    if not plotted_any_graph:
        print(
            "Nothing to plot yet: pass vqf_cost_history_sim/hw and/or "
            "scale_factors + target_probs_by_scale."
        )
