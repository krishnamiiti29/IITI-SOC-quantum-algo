# Quantum Valorant

Two-phase hybrid quantum pipeline for IITISoC 2026: Shor's algorithm (via Iterative Quantum Phase Estimation) factors a composite `N` into `(Width, Height)`, and a parity-constrained Grover search then hunts for a hidden `(x, y)` key on that `Width x Height` lattice using a fixed π/3 phase oracle.

This README explains **every file** in the pipeline, in the order they actually run, including what each function does internally, what quirks/known bugs exist, and how the pieces connect.

---

## How a run actually flows (`Runner.py`)

`Runner.py` is the entry point. In order, it:

1. **`GiveN()`** (`Customize.py`) — picks the target composite number `N` to factor. Currently hardcoded to a single-element pool `[95]`.
2. **`CreateDimension(N)`** (`Internal/DimensionGen.py`) — finds a valid `(width, height)` factor pair of `N` classically (brute-force trial division up to `sqrt(N)`), purely so the script has a **ground-truth pair to print/compare against**. This is *not* how the algorithm actually determines the factors — that's Shor's job below.
3. **`GenerateKey(Dimensions)`** (`Internal/GenerateKey.py`) — picks a random valid `(x, y)` "key" on that lattice, printed as the target for Phase 2. See the **"double key generation" issue** below — this printed key is *not* guaranteed to be the same key Phase 2 later searches for.
4. **Phase 1 loop** — calls `ApplyPhase1(N)` up to `MAX_ATTEMPTS = 20` times. Each attempt runs one IQPE circuit and tries to recover a factor. Shor's algorithm is probabilistic (a bad choice of random base, or an odd/unlucky order, causes failure), so the retry loop exists to survive that.
5. Once factors are found, `Width, Height = factors_discovered` — these are the **real, quantum-recovered** dimensions.
6. **Phase 2** — `ApplyPhase2(Width, Height)` builds and runs the Grover search circuit and reports whether the target key was found.

---

## `Customize.py` — configuration

Three things live here:

- `IBM_API_KEY`, `IBM_INSTANCE_CRN` — your IBM Quantum Platform credentials. Currently placeholder joke strings, not real values — **you must fill these in with real credentials before hardware runs will work.** Both `Phase1.py` and `Phase2.py` import these directly and pass them into `QiskitRuntimeService(...)`.
- `GiveN()` — returns a random choice from a hardcoded `N_list`. Right now the list only contains `95` (`= 5 × 19`). The comment says other confirmed-working values are `57, 111, 123` — you'd add them to the list to use them, they aren't wired in currently.

**Do not commit real credentials.** Prefer pulling `IBM_API_KEY` from an environment variable instead of hardcoding it in this file, and rotate the key immediately if it's ever pushed live.

---

## `Internal/` — shared utilities used by both phases

### `DimensionGen.py`

```python
CreateDimension(N)
```
Trial-divides `N` by every `i` from `2` to `sqrt(N)`, collects every `[i, N//i]` pair where `i` divides `N` evenly, and returns one such pair **at random**. For a semiprime like `95 = 5 × 19`, there's only one valid pair, so the randomness doesn't matter in practice — but if `N` had multiple factorizations, this would pick unpredictably among them.

### `GetHammingWeight.py`

```python
GiveHammingWeight(x)
```
Converts `x` to binary and counts the number of `1` bits (its Hamming weight / `popcount`). This single function underlies both the key-generation logic and the Grover oracle's marking condition.

### `GenerateKey.py`

```python
GenerateKey(Dimension)   # Dimension = [x_max, y_max]
```
This is the classical definition of "what counts as a valid key" — the same rule the Grover oracle is built to search for quantum-mechanically. Logic:

1. Computes `TargetWeightSum = HammingWeight(x_max) + HammingWeight(y_max)` — a "target" derived from the *factor pair itself*.
2. Loops `i` over **even values only** (`range(0, x_max, 2)`) — a deliberate constraint (the code comment jokingly attributes this to "the PS" — the project spec).
3. For each even `i` and every `j` in `range(y_max)`, checks if `HammingWeight(i) XOR HammingWeight(j) == TargetWeightSum`. If so, `[i, j]` is a valid key candidate.
4. Returns **one random candidate** from the list of matches (or `None` if no candidate exists).

**Important non-determinism:** because step 4 picks randomly among possibly many valid keys, calling `GenerateKey` twice with the same dimensions can return *different* keys. This matters — see the flagged issue below.

### `SpaceGen.py`

Two constructors for the quantum register scaffolding, both just wrapping a `QuantumRegister`/`QuantumCircuit` pair:

- `CreateSpace(N)` — internally calls `CreateDimension(N)` to pick `(w, h)`, then builds a circuit with a `Width` register of `w` qubits and a `Height` register of `h` qubits.
- `CreateSpaceDimensioned(Width, Height)` — same, but takes the width/height qubit counts directly instead of deriving them from `N`. This is the one actually used later, by `EvenSuperposition.py`.

### `Phases/Initiation.py`

```python
Initiate(N) -> (Space, Dimensions, Key)
```
A convenience wrapper that chains `CreateSpace` + `GenerateKey`. **Not called anywhere in `Runner.py` or either phase** — it's a leftover/unused helper, most likely from an earlier version of the pipeline before Phase 1/Phase 2 were split out.

---

## Phase 1 — Shor's algorithm via Iterative QPE

Goal: factor `N` using order-finding, without knowing the factors in advance.

### `Shors_Algorithm/Setup.py`

```python
ChooseGamma(N)
```
Builds the list of all integers `1 < i < N` that are coprime to `N` (`gcd(i, N) == 1`), and picks one at random. This is the base `Γ` ("a") whose multiplicative order mod `N` we're trying to find — the standard first step of Shor's algorithm.

### `Shors_Algorithm/BuildUnitary.py`

```python
BuildUnitary(Gamma, N) -> Operator
power_of_unitary(U, exponent) -> Operator
```
This is the "cheat" (but standard for small-N demos) way of implementing modular multiplication as a quantum gate, instead of building a real reversible modular-arithmetic circuit:

1. Works in a `dim = 2**ceil(log2(N))` dimensional space (the smallest power-of-2 that can hold `N`).
2. For every `x` coprime to `N`, maps it to `(x * Gamma) % N` — this is the actual "multiply by Γ mod N" action.
3. Because `dim` is generally *larger* than `N` (padding to a power of 2), and because only the coprime residues have a "real" destination under this map, the leftover indices (`x >= N` or `gcd(x,N) != 1`) are patched into whatever destination slots remain unused, purely so the whole thing stays a valid permutation matrix (i.e. a valid unitary). These "bridge" mappings are mathematically meaningless — they only exist to keep the operator unitary; the real dynamics only apply to numbers coprime to `N`.
4. The permutation is turned into a literal permutation matrix and wrapped in Qiskit's `Operator`.

`power_of_unitary` computes `U^exponent` (needed for the controlled-`U^(2^k)` gates in IQPE) by literally matrix-powering the array, then **snaps each column back to a clean permutation matrix** by keeping only the largest-magnitude entry and zeroing the rest — this scrubs floating-point noise that would otherwise accumulate from repeated matrix multiplication and could make the "unitary" fail the unitarity check.

This whole approach only scales to small `N` (dense `2^n x 2^n` matrices), which is why the project is validated on small semiprimes like 95, 111, 123.

### `Shors_Algorithm/IQPE/CircuitGen.py`

```python
build_iqpe_circuit(U, precision) -> QuantumCircuit
```
Builds a **bit-by-bit Iterative Quantum Phase Estimation** circuit (Kitaev's algorithm) instead of the textbook full-QFT version — this needs only **1 phase qubit total** (reused/reset every round) instead of `precision` phase qubits, which is why it's much cheaper on real hardware.

- `system` register: `n = U.num_qubits` qubits, initialized to `|1⟩` (`circuit.x(system[0])`) as a placeholder eigenstate-overlap starting state — standard for Shor-style order finding, since `|1⟩` has overlap with all the eigenstates of the modular-multiplication operator.
- Loop runs `precision - 1` down to `0` (most-significant estimated bit first... actually least significant bit of the phase is estimated last, in Kitaev ordering):
  - Reset & Hadamard the single phase qubit.
  - Apply **controlled-`U^(2^k)`** — built by matrix-powering `U` via `power_of_unitary` and wrapping it as a controlled `UnitaryGate`.
  - **Classical feedback**: for every previously-measured bit `j > k`, conditionally apply a phase correction `angle = -π / 2^(j-k)` using `circuit.if_test(...)` — this is the "kickback correction" that lets IQPE use only 1 phase qubit instead of `precision` of them.
  - Hadamard again, then measure into `phase_bits[k]`.

Returns a circuit with `precision` classical bits holding the estimated phase, most-significant bit first.

### `Shors_Algorithm/IQPE/ClassicalPostProcess.py`

```python
bitstring_to_phase(bitstring)
estimate_order_from_counts(counts, a, N)
```
Converts each measured bitstring into a phase estimate `∈ [0,1)`, tries every distinct measurement result **starting with the most frequent**, and for each one attempts to recover an order `r` via continued fractions (below). Returns the first candidate `r` that actually verifies (`a^r mod N == 1`), or `None` if nothing works.

### `Shors_Algorithm/IQPE/OrderRecovery.py`

```python
continued_fraction_order(phase, a, N)
```
The core number-theory step of Shor's algorithm: given an estimated phase `≈ s/r`, uses Python's `Fraction(...).limit_denominator(N)` to find the best rational approximation with denominator `≤ N`. That denominator is the candidate order `r`. It's only accepted if `a^r mod N == 1` actually holds — otherwise this measurement is a dud and the caller (`estimate_order_from_counts`) moves on to the next most-frequent bitstring.

### `Shors_Algorithm/FindFactor.py`

```python
recover_factors(a, N, r)
```
Standard Shor's post-processing:

1. Bails out if `r` is `None` or odd (order-finding needs an even order for this trick to work).
2. Computes `x = a^(r/2) mod N`. Bails out if `x == N-1` (a trivial/degenerate case where `gcd` won't give a useful factor).
3. `factor_1 = gcd(x-1, N)`, `factor_2 = gcd(x+1, N)` — the classic Shor's algorithm factor extraction.
4. Bails out (`None`) if either factor is trivial (`1` or `N`).
5. **The swap block has a real bug** — it's meant to guarantee `factor_1` ends up as the larger of the two:
   ```python
   if factor_1 < factor_2:
       tempfactor = factor_2
       factor_2 = factor_1
       factor_1 = factor_2   # BUG: factor_1 is unchanged, factor_2 already got overwritten above
   factor_2 = N // factor_1
   ```
   `tempfactor` is computed and never used; the intended swap is a no-op, so `factor_1` never actually changes here. **In practice this doesn't corrupt the final result**, because the very next line unconditionally recomputes `factor_2 = N // factor_1` — since `N = factor_1 * factor_2` exactly, this recovers the correct co-factor regardless of which one `factor_1` originally was. So it's dead/broken logic, but not a correctness bug given the current code around it — worth cleaning up for clarity, not urgent to fix.
6. `Phase1.py` separately re-sorts the returned tuple (`if factors[0] > factors[1]: swap`) so the final `(Width, Height)` handed to Phase 2 is always ascending — this is where the ordering actually gets enforced, independent of the dead swap above.

### `External Testing/ClassicalCheck.py`

```python
find_order_classically(a, N)
```
Brute-force reference implementation (multiply by `a` repeatedly until you hit `1 mod N`) used **only to verify** the quantum order-finding is working correctly during development. The in-file comment is explicit that this must not be part of the real hardware pipeline — it's exponential and defeats the purpose of using Shor's algorithm at all, it's for testing/debugging only. It isn't imported anywhere in `Runner.py`/`Phase1.py`, so it's already correctly excluded from the live pipeline.

### `Phases/Phase1.py`

```python
ApplyPhase1(N) -> (Width, Height) | None
```
Ties the above together for one attempt:

1. `ChooseGamma(N)` → random coprime base.
2. `BuildUnitary(Gamma, N)` → the permutation operator.
3. `build_iqpe_circuit(U, precision=8)` — phase estimated to 8 bits.
4. **Backend selection with fallback**: tries to connect to `QiskitRuntimeService` and grab the least-busy real IBM backend with `min_num_qubits = precision` (i.e. 8). If that connection fails for any reason (bad credentials, no internet, IBM outage), it silently falls back to a local `AerSimulator` instead of crashing.
   - **Caveat worth knowing**: `min_num_qubits=precision` (8) doesn't account for the *system register* size needed by the IQPE circuit — `build_iqpe_circuit` also allocates `n = U.num_qubits = ceil(log2(dim))` system qubits (for `N=95`, `dim=128`, so `n=7` system qubits) plus 1 phase qubit = up to 8 total already, and this can grow for larger `N`. If you push `N` much larger than the demo values, an 8-qubit backend request could end up too small for the transpiled circuit.
5. Transpiles with `generate_preset_pass_manager(optimization_level=1, ...)`.
6. Runs 1024 shots — via `SamplerV2` if on real hardware, or `backend.run(...)` directly if on `AerSimulator`.
7. Feeds the resulting counts into `estimate_order_from_counts` → `recover_factors`.
8. If factors are found, sorts them ascending and returns `(Width, Height)`; otherwise returns `None` (and `Runner.py`'s loop tries again, up to 20 times).

---

## Phase 2 — Parity-restricted Grover search

Goal: given the recovered `(Width, Height)`, find a hidden `(x, y)` key satisfying the same Hamming-weight-parity rule that `GenerateKey.py` uses, via Grover's algorithm.

### `Phases/Phase_2/EvenSuperposition.py`

```python
CreateEvenSuperposition(width, height) -> QuantumCircuit
```
Builds the initial search-space superposition:

- **All** height qubits get a Hadamard → full superposition over every `y` value.
- **All width qubits except the least-significant bit (index 0)** get a Hadamard → superposition over every **even** `x` value only (the LSB is left at `|0⟩`, forcing `x` to always be even). This matches the "even x only" constraint baked into `GenerateKey.py`.

### `Phases/Phase_2/Oracle.py` — the actual oracle used in the live pipeline

```python
PI3_ANGLE = π/3

ApplyHammingWeightOracle(QC, width, height, target_parity, angle=PI3_ANGLE)
BuildDiffuser(num_qubits, angle=PI3_ANGLE)
BuildGroverCircuit(QC, width, height, target_parity, iterations=8, angle=PI3_ANGLE)
```

How the oracle works, mechanically:

1. It **classically enumerates every matching basis state** — for every even `x` in `[0, 2^width)` and every `y` in `[0, 2^height)`, it checks whether `HammingWeight(x) XOR HammingWeight(y)` matches `target_parity`.
2. For each match, it: flips (X-gates) whichever qubits should read `0` in that specific `(x,y)`, applies a **multi-controlled phase gate** (`MCPhaseGate(π/3)`, controlled on *all* search qubits being `1`) to imprint the π/3 phase specifically onto that one basis state, then un-flips the same qubits.
3. This repeats independently for every single matching `(x,y)` pair — i.e. the oracle is built as a **literal sum of individually-marked basis states**, not a compact arithmetic circuit. For small `width+height` this is workable, but the gate count/circuit depth scales with the *number of matching states*, which can be large.

`BuildDiffuser` is the standard "inversion about the mean" diffuser (`H → X → MCPhase(angle) → X → H`), but — notably — it's called with the **same `angle = π/3`** as the oracle, not `π` (a full reflection).

`BuildGroverCircuit` just loops `iterations` (hardcoded to `8` in `Phase2.py`) rounds of oracle-then-diffuser.

**Why this matters:** using `ψ = π/3` for the diffuser (instead of `ψ = π`, a full reflection) roughly halves the per-iteration rotation strength, meaning it takes more Grover iterations to converge to the same success probability than a full-reflection diffuser would need. `GROVER_ITERATIONS = 8` is a fixed constant in `Phase2.py`, not derived from any optimal-iteration-count formula, so there's currently no guarantee 8 iterations is actually optimal for a given `Width`/`Height`.

### `Phases/Phase_2/Mitigation.py` — now called from `Phase2.py`

```python
RunWithMitigation(GroverCircuit, backend, key, width, height, scale_factors=(1), shots=2048)
```
A full three-layer error-mitigation stack intended for running the Grover circuit on **real IBM hardware**:

1. **Dynamical decoupling (XY4) + gate/measurement twirling** — turned on via `SamplerV2` options (`sampler.options.dynamical_decoupling.enable = True`, etc.) rather than manually inserted gates.
2. **Zero-noise extrapolation via unitary folding** — `_fold_circuit` implements `U → U (U⁻¹U)^k` at each odd `scale_factor`, runs each folded circuit, and `_zne_extrapolate` fits a polynomial (degree = `order`, default linear) through the `(scale, P(target))` points and extrapolates to `scale = 0` — the noise-free estimate.
3. **M3 readout correction** — `_m3_correct` uses `mthree.M3Mitigation` to build a calibration and correct the raw counts, but is **skipped** and replaced with plain normalized counts when the backend is a local `AerSimulator` (there's no readout noise to correct against on a simulator).

**Known bug**: the default argument `scale_factors=(1)` is a plain integer `1`, not a one-element tuple `(1,)` — Python parses `(1)` as just `1` due to the missing comma. If this function is ever called *without* explicitly passing `scale_factors`, the `for sf in scale_factors:` loop will crash trying to iterate over an int. It currently isn't called with defaults anywhere, but it also isn't called at all right now (see next section), so this hasn't surfaced yet.

`Phase2.py` now imports and calls `RunWithMitigation` when running on real hardware.

### `Phases/Phase_2/HeatmapGen.py`

```python
decode_bitstring(bitstring, width, height) -> (x, y)
counts_to_probability_grid(counts, width_qubits, height_qubits, Width, Height) -> (grid, leaked_p)
PlotHeatmap(counts, width_qubits, height_qubits, Width, Height, key=None, title=..., save_path=None)
```
- `decode_bitstring` reverses Qiskit's bit-ordering convention to recover `(x, y)` from a measured bitstring, matching the encoding used elsewhere (search qubits `[0..width-1]` = x, `[width..width+height-1]` = y).
- `counts_to_probability_grid` turns raw shot counts into a probability grid **clipped to the real `Width x Height` lattice** — because the qubit count is `ceil(log2(Width))`-style rounding, the computational basis is usually padded larger than the real lattice (e.g. `Width=14` needs 4 qubits, covering `x ∈ [0,16)`, but only `[0,14)` are "real" grid cells). Any probability landing outside the real lattice is tallied separately as `leaked_p` rather than silently dropped or miscounted.
- `PlotHeatmap` renders this grid with `matplotlib`, stars the target key if given, prints/saves the figure, and returns `(fig, grid, leaked_p)`.

**Assumes a noiseless simulator** — raw counts are treated directly as probabilities, no mitigation is applied inside this file (mitigation, if used, is expected to happen upstream before counts get here).

### `Phases/Phase2.py` — orchestrates Phase 2

```python
ApplyPhase2(Width, Height) -> dict | None
```

1. Computes `width_qubits = ceil(log2(Width+1))`, `height_qubits = ceil(log2(Height+1))` — enough bits to represent the real dimensions.
2. **Calls `GenerateKey([Width, Height])` again** — a *second, independent* call to the same random-key-picking function `Runner.py` already called once at the top of the script. Since `GenerateKey` picks randomly among possibly multiple valid keys, **this can produce a different key than the one `Runner.py` printed as "Target Key" at the start** — Phase 2 searches for whichever key it *just* generated, not necessarily the one shown earlier in the console log. Worth deciding whether the key should be generated once and threaded through, rather than regenerated here.
3. Computes `target_parity` from the Hamming weights of `Width` and `Height` directly (not from the key) — this matches how the oracle in `Oracle.py` is parameterized.
4. Builds the superposition (`CreateEvenSuperposition`) and the Grover circuit (`BuildGroverCircuit`, 8 iterations, hardcoded).
5. **Now runs through `RunWithMitigation`** (`Mitigation.py`) instead of a plain `backend.run(...)` call — so the full DD (XY4) + gate/measurement twirling + ZNE (unitary folding) + M3 readout-correction stack is applied when Phase 2 executes on real hardware, rather than being dead code.
6. **Bug to flag**: the function calls `PlotHeatmap(...)` at the end, but `PlotHeatmap` is never imported into `Phase2.py` (only `CreateEvenSuperposition`, `BuildGroverCircuit`, `RunWithMitigation`, `GenerateKey`, `GiveHammingWeight` are imported). As written, this will raise a `NameError: name 'PlotHeatmap' is not defined` the moment `ApplyPhase2` reaches that line. Fix: add `from FilePipeline.Phases.Phase_2.HeatmapGen import PlotHeatmap` at the top of `Phase2.py`.
7. Reports `P(target)` — the measured probability of the target key's bitstring — and declares `found = P(target) >= 0.5`, returning a dict with the circuit, key, probability grid, counts, and the heatmap figure.

---

## Known issues (collected from actual source, not assumptions)

| # | File | Issue |
|---|------|-------|
| 1 | `Phase2.py` | `PlotHeatmap` is called but never imported — will crash with `NameError` on every real run right now. |
| 2 | `Phase2.py` / `Runner.py` | `GenerateKey` is called twice independently (once in `Runner.py` for display, once inside `ApplyPhase2`); since it returns a random valid key each call, the two can differ. |
| 3 | `Phase_2/Oracle.py` | Diffuser uses `ψ = π/3` (same angle as the oracle) instead of a full `ψ = π` reflection, which weakens the per-iteration rotation and likely means more than 8 iterations are needed to converge well. |
| 4 | `Phase_2/Mitigation.py` | `RunWithMitigation` default `scale_factors=(1)` is an int, not a tuple — will crash with a `TypeError`/iteration error if `Phase2.py` ever calls it without explicitly passing `scale_factors`. Worth double-checking the call site passes a real tuple like `(1, 3, 5)`. |
| 5 | `Shors_Algorithm/FindFactor.py` | The `factor_1 < factor_2` swap block is logically broken (doesn't actually swap), but is functionally harmless because `factor_2 = N // factor_1` is unconditionally recomputed right after. Worth cleaning up, not urgent. |
| 6 | `Phase1.py` | Backend qubit-count request (`min_num_qubits=precision=8`) doesn't account for the IQPE circuit's system register size, which can exceed 8 for larger `N`. |
| 7 | `Customize.py` | `IBM_API_KEY` / `IBM_INSTANCE_CRN` are placeholder strings, not real credentials — must be filled in before any real-hardware run will succeed. |
| 8 | `Phases/Initiation.py` | `Initiate()` is unused dead code — not called from `Runner.py` or either phase file. |

---

## Setup

```bash
pip install qiskit qiskit-aer qiskit-ibm-runtime mthree numpy matplotlib
```

Set credentials in `Customize.py` (or better, load `IBM_API_KEY` from an environment variable rather than hardcoding it):

```python
IBM_API_KEY = "<your IBM Quantum API key>"
IBM_INSTANCE_CRN = "<your instance CRN, or None>"
```

Run:

```bash
python Runner.py
```

## Configuration

- `Customize.py::GiveN()` — pool of valid `N` values to test, currently just `[95]`. Confirmed-working values noted in-code: `57, 95, 111, 123`.
- `Phase1.py` — IQPE `precision = 8` bits; `Runner.py` retries up to `MAX_ATTEMPTS = 20` times.
- `Phase2.py` — `GROVER_ITERATIONS = 8`, a hardcoded module-level constant, not derived from the oracle's marked-state density (see issue #3/#5 above — revisit if `Width`/`Height` change significantly, or if the diffuser angle is ever corrected to `ψ = π`).
