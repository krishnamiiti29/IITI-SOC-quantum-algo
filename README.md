# Quantum Valorant

Two-phase hybrid quantum pipeline for IITISoC 2026: Shor's algorithm (via Iterative QPE) factors a composite `N`, and the recovered factors seed a parity-constrained Grover search with a fixed-point π/3 phase oracle. Phase 2 runs under a four-layer hardware error mitigation stack (DD/XY4, Pauli twirling, ZNE via unitary folding, M3 readout correction).

## Pipeline

```
Runner.py
 ├─ GiveN()                         → target composite N (Customize.py)
 ├─ CreateDimension(N)              → candidate (width, height) factor pair
 ├─ GenerateKey(Dimensions)         → target (x, y) key for Phase 2
 │
 ├─ Phase 1 — Shor / IQPE           (retried up to MAX_ATTEMPTS=20)
 │   ├─ ChooseGamma(N)              → random Γ coprime to N
 │   ├─ BuildUnitary(Γ, N)          → permutation matrix for ×Γ mod N
 │   ├─ build_iqpe_circuit(U, 8)    → 1 phase qubit + system register, bit-by-bit IQPE
 │   ├─ backend: least-busy IBM QPU, falls back to AerSimulator on connection failure
 │   ├─ estimate_order_from_counts  → continued-fraction order recovery
 │   └─ recover_factors(Γ, N, r)    → (Width, Height)
 │
 └─ Phase 2 — Parity-Restricted Grover
     ├─ CreateEvenSuperposition     → H⊗ on all height qubits, H⊗ on width qubits[1:] (LSB pinned to 0)
     ├─ BuildGroverCircuit          → GROVER_ITERATIONS × (ApplyHammingWeightOracle + BuildDiffuser), angle = π/3
     ├─ backend: least-busy IBM QPU, min 10 qubits
     └─ PlotHeatmap                 → P(x, y) grid over the true Width×Height lattice, target key starred
```

## File map

```
Customize.py                    IBM_API_KEY, IBM_INSTANCE_CRN, GiveN() — edit per run
Runner.py                       top-level orchestration, Phase 1 retry loop

FilePipeline/Internal/
  DimensionGen.py                CreateDimension — factor pairs of N
  GenerateKey.py                 GenerateKey — Hamming-weight-XOR key search
  GetHammingWeight.py             GiveHammingWeight
  SpaceGen.py                    CreateSpace / CreateSpaceDimensioned — register scaffolding
  Initiation.py                  Initiate — unused convenience wrapper (Space, Dims, Key)

FilePipeline/Shors_Algorithm/
  Setup.py                       ChooseGamma — random coprime base
  BuildUnitary.py                permutation unitary for ×Γ mod N, power_of_unitary
  FindFactor.py                  recover_factors — gcd(a^{r/2} ± 1, N)
  ClassicalCheck.py              find_order_classically — verification only, NOT for hardware runs
  IQPE/
    CircuitGen.py                build_iqpe_circuit — bit-by-bit IQPE with classical feedback
    ClassicalPostProcess.py      estimate_order_from_counts
    OrderRecovery.py             continued_fraction_order

FilePipeline/Phases/
  Phase1.py                      ApplyPhase1 — circuit build, transpile, submit, factor recovery
  Phase2.py                      ApplyPhase2 — search-space setup, oracle, measurement, heatmap
  Phase_2/
    EvenSuperposition.py          CreateEvenSuperposition
    Oracle.py                    ApplyHammingWeightOracle, BuildDiffuser, BuildGroverCircuit
    Mitigation.py                RunWithMitigation — DD+twirl+ZNE+M3 stack (currently unused by Phase2.py)
    HeatmapGen.py                PlotHeatmap, counts_to_probability_grid, decode_bitstring
```

## Setup

```bash
pip install qiskit qiskit-aer qiskit-ibm-runtime mthree numpy matplotlib
```

Set credentials in `Customize.py`:

```python
IBM_API_KEY = "<your IBM Quantum API key>"
IBM_INSTANCE_CRN = "<your instance CRN, or None>"
```

**Do not commit real credentials.** This file has been the source of a repeated leaked-token/401 issue — rotate immediately if it's ever pushed with a live key, and prefer pulling `IBM_API_KEY` from an environment variable instead of hardcoding it.

Run:

```bash
python Runner.py
```

## Configuration

- `Customize.py::GiveN()` — pool of valid `N`, currently `[95]`. Confirmed-working values: `57, 95, 111, 123`.
- `Phase1.py` — IQPE `precision = 8` bits, `MAX_ATTEMPTS = 20` retries in `Runner.py`.
- `Phase2.py` — `GROVER_ITERATIONS = 8`, hardcoded module-level constant (not derived from the oracle's marked-state density; revisit if `Width`/`Height` change significantly).

## Known open issues

- **`Mitigation.py` is not wired into `Phase2.py`.** `ApplyPhase2` runs a bare `backend.run(...)` with no DD/twirling/ZNE/M3 — the full mitigation stack in `Mitigation.py` (DD XY4, gate/measurement twirling, unitary-folded ZNE, M3 readout correction) is implemented but currently dead code. `Phase2.py` also references `PlotHeatmap` without importing it from `HeatmapGen.py`.
- **`Mitigation.py::RunWithMitigation` default arg bug** — `scale_factors=(1)` is an int, not a tuple; iterating over it will fail. Should be `(1,)` or `(1, 3, 5)`.
- **`FindFactor.py::recover_factors` swap bug** — the `factor_1 < factor_2` branch assigns `factor_2 = factor_1` before the swap completes (both ends up holding the original `factor_1`). Dead/no-op swap logic.
- **Backend qubit-count mismatch risk** — Phase 1 requests `min_num_qubits=precision` (8) while Phase 2 requests `min_num_qubits=10`; neither accounts for the system register size in Phase 1's IQPE circuit (`num_qubits = ceil(log2(N))` + 1 phase qubit), which can exceed what a small backend supports post-transpile.
- **`GenerateKey.py`** iterates only even `x` in `range(0, x, 2)` (note: loop bound reuses the parameter name `x`, shadowing it) — confirm this matches the intended even-width constraint from `EvenSuperposition.py` before large `N` runs.

## Error mitigation stack (`Mitigation.py`, intended for Phase 2)

1. **Dynamical decoupling (XY4)** + **gate/measurement twirling** — applied per-job via `SamplerV2` options.
2. **Zero-noise extrapolation** — unitary folding `U → U(U⁻¹U)^k` at odd scale factors (1, 3, 5, ...), linear extrapolation to the zero-noise limit via `np.polyfit`.
3. **M3 readout correction** — `mthree.M3Mitigation`, skipped and replaced with raw normalized counts when running on `AerSimulator` (no readout noise to correct).

Output: ZNE-extrapolated `P(target key)`, per-scale probabilities, and raw counts at each scale factor.
