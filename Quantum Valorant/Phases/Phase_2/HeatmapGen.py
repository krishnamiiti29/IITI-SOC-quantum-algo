"""
FilePipeline/Phases/Phase_2/HeatmapGen.py

Builds a 2D probability heatmap over the (x, y) search-register lattice.
Each lattice cell (x, y) is colored by the probability of that basis
state being measured when the key-state is prepared and run through the
Grover circuit.

This assumes a NOISELESS classical simulator (AerSimulator, no noise
model) -- raw counts/shots are treated directly as probabilities. No
mitigation (ZNE/M3/twirling) is applied or needed here.

Nothing in Phase 1, Runner.py, EvenSuperposition.py, GenerateKey.py,
Oracle.py, or any other existing file is modified.
"""

import numpy as np
import matplotlib.pyplot as plt


def decode_bitstring(bitstring, width, height):
    """
    Decode a Qiskit measurement bitstring back into (x, y).

    Inverts the exact convention used by Mitigation._key_to_bitstring:
    qubit i of the search register (x_qubits = [0..width-1],
    y_qubits = [width..width+height-1]) maps to character
    bitstring[n-1-i] in Qiskit's returned string (classical bit 0 is
    rightmost).
    """
    rev = bitstring[::-1]  # rev[i] == bit measured on qubit i
    x_bits = rev[0:width]
    y_bits = rev[width:width + height]
    x = int(x_bits[::-1], 2) if width > 0 else 0
    y = int(y_bits[::-1], 2) if height > 0 else 0
    return x, y


def counts_to_probability_grid(counts, width_qubits, height_qubits, Width, Height):
    """
    Convert raw measurement counts into a 2D probability grid, clipped to
    the ACTUAL lattice size (Width x Height) rather than the full
    2**width_qubits x 2**height_qubits computational basis.

    Qubit counts are always >= the factor values themselves (they're the
    minimum bits needed to represent them), so the computational basis is
    generally bigger than the real lattice -- e.g. Width=14 needs 4 qubits
    but that covers x in [0, 16), only [0, 14) of which are real. Any
    measured (x, y) that falls outside the real lattice is invalid --
    it's tallied separately as "leaked" probability instead of being
    silently dropped.

    Returns
    -------
    grid     : np.ndarray, shape (Width, Height)
        grid[x, y] = P(measuring basis state |x, y>), for x < Width, y < Height
    leaked_p : float -- total probability measured outside [0,Width)x[0,Height)
    """
    total_shots = sum(counts.values())
    grid = np.zeros((Width, Height))
    leaked_p = 0.0

    for bitstring, count in counts.items():
        x, y = decode_bitstring(bitstring, width_qubits, height_qubits)
        p = count / total_shots
        if x < Width and y < Height:
            grid[x, y] += p
        else:
            leaked_p += p

    return grid, leaked_p


def PlotHeatmap(counts, width_qubits, height_qubits, Width, Height, key=None,
                 title="Key-State Preparation Probability", save_path=None):
    """
    Plot (and optionally save) a 2D heatmap of P(x, y) over the ACTUAL
    Width x Height lattice (not the padded 2**qubits computational basis).

    Parameters
    ----------
    counts        : dict[str, int] -- raw counts from AerSimulator (noiseless)
    width_qubits  : int   -- qubits used to encode x (>= ceil(log2(Width+1)))
    height_qubits : int   -- qubits used to encode y (>= ceil(log2(Height+1)))
    Width, Height : int   -- the real factor dimensions, i.e. plot size
    key           : [x, y], optional -- marks the target key with a star
    title         : str
    save_path     : str, optional -- PNG path to save the figure to

    Returns
    -------
    fig      : matplotlib Figure
    grid     : np.ndarray, shape (Width, Height) -- the probability grid
    leaked_p : float -- probability measured outside the valid lattice
    """
    grid, leaked_p = counts_to_probability_grid(
        counts, width_qubits, height_qubits, Width, Height
    )

    fig, ax = plt.subplots(figsize=(6, 6))
    im = ax.imshow(grid.T, origin="lower", cmap="viridis", aspect="auto")

    ax.set_xlabel("x  (Width lattice index)")
    ax.set_ylabel("y  (Height lattice index)")
    ax.set_title(title)
    ax.set_xticks(range(Width))
    ax.set_yticks(range(Height))

    if key is not None:
        ax.scatter([key[0]], [key[1]], marker="*", s=280,
                   facecolors="none", edgecolors="red", linewidths=2,
                   label="Target key")
        ax.legend(loc="upper right")

    fig.colorbar(im, ax=ax, label="Probability")
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"  Heatmap saved to {save_path}")

    print(f"  Probability outside the {Width}x{Height} lattice (leaked): {leaked_p:.4f}")

    plt.show()

    return fig, grid, leaked_p