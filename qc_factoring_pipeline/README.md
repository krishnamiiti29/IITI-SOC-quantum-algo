# Quantum Factoring Pipeline

This is the original `QC_4_16.ipynb` notebook broken apart into a proper
Python package: one function (or tightly related group of functions) per
file, organized into a pipeline you can run stage-by-stage or end to end.

No logic was changed — every function is a straight extraction from the
notebook, including the inline comments/warnings the original author left
behind. Only the organization is new.

## Structure

```
qc_factoring_pipeline/
├── main.py                        # End-to-end simulator-only pipeline (Phase 1 + Phase 2/3)
├── requirements.txt
├── qc_pipeline/                   # The actual library code
│   ├── config.py                  # NUMBER_CHOICES, ancilla count, etc.
│   ├── utils/
│   │   └── dimension_utils.py     # DimensionGiver, GiveHammingWeight, GiveParity, KeyChoice, GiveQubitCount
│   ├── space_prep/
│   │   ├── initiate.py            # Initiate() — allocates registers/circuit, picks N
│   │   └── classical_order_finding.py  # BuildUnitary, RunIter, ProvideDimensions
│   ├── quantum_order_finding/
│   │   ├── qpe_circuit.py         # BuildControlledPowerGate, BuildQPEOrderFindingCircuit, PhaseToOrder
│   │   └── qpe_runner.py          # ProvideDimensionsQuantum (sim or real backend)
│   ├── vqf/
│   │   ├── hamiltonian.py         # build_vqf_hamiltonian (QUBO/Ising cost)
│   │   └── runner.py              # run_vqf (QAOA, sim or real backend)
│   ├── grover/
│   │   ├── superposition.py       # CreateConstrainedEvenSuperposition
│   │   ├── oracle.py              # ApplyHammingWeightResonanceOracle, build_pi3_diffuser
│   │   └── decode.py              # decode_bitstring, key_to_bitstring, decode_counts
│   ├── hardware/
│   │   ├── backend_selection.py   # select_backend, save_ibm_account, qpe_qubits_needed
│   │   └── mitigation.py          # make_mitigated_sampler, fold_circuit_global, m3_mitigate_counts, zne_extrapolate
│   └── visualization/
│       └── plots.py               # plot_full_distribution, plot_qaoa_convergence, plot_zne_fit
└── scripts/                        # Runnable pipeline stages (mirror the notebook's cell order)
    ├── run_classical_pipeline.py       # Phase 1 (cells 0-3)
    ├── run_qpe_demo.py                 # QPE order finding, sim + optional hardware (cells 6-8)
    ├── run_vqf_demo.py                 # VQF/QAOA factoring, sim + optional hardware (cells 11-12)
    ├── run_grover_pipeline.py          # Phase 2/3 build + simulate + decode (cells 14-15)
    ├── run_grover_hardware.py          # Phase 2/3 on real IBM hardware (cells 17-18)
    ├── run_grover_hardware_mitigated.py# Grover + DD/twirling/ZNE/M3 (cell 21)
    └── run_plots.py                    # Plot whatever results you've collected (cells 19, 22)
```

## Install

```bash
pip install -r requirements.txt
```

## Quick start (simulator only, no IBM account needed)

```bash
python main.py
```

This runs Phase 1 (pick N, classically find a factor pair) followed by
Phase 2/3 (build the oracle/diffuser circuit and simulate it), printing the
top measured `(x, y)` pairs and whether the target key was found.

## Running individual stages

Each script under `scripts/` can be run standalone; most will fall back to
running Phase 1 for you if you don't hand them `N`/`Space`/etc. directly.

```bash
# Classical order finding only
python scripts/run_classical_pipeline.py

# QPE-based order finding (simulator)
python scripts/run_qpe_demo.py --N 6

# QPE on real IBM hardware too (requires a saved IBM Quantum account)
python scripts/run_qpe_demo.py --N 6 --hardware

# VQF/QAOA factoring (simulator)
python scripts/run_vqf_demo.py --N 21

# VQF on real hardware (COST WARNING: many hardware jobs per run — see script docstring)
python scripts/run_vqf_demo.py --N 21 --hardware --maxiter 20

# Grover build + simulate + decode
python scripts/run_grover_pipeline.py

# Grover on real hardware
python scripts/run_grover_hardware.py

# Grover on real hardware with full error mitigation (DD + twirling + ZNE + M3)
python scripts/run_grover_hardware_mitigated.py
```

## Using an IBM Quantum backend

Any script with a `--hardware` flag, or the hardware scripts, need a saved
IBM Quantum Platform account. One-time setup:

```python
from qc_pipeline.hardware.backend_selection import save_ibm_account
save_ibm_account(token="YOUR_IBM_CLOUD_API_KEY", instance="YOUR_INSTANCE_CRN")
```

Get both values from https://quantum.cloud.ibm.com (dashboard = API key,
Instances tab = CRN).

## Notes carried over from the original notebook

- Phase 2's `CreateConstrainedEvenSuperposition` deliberately excludes qubit
  0 (the LSB) from the Hadamard layer so every `x` in the superposition
  stays even, matching `KeyChoice`'s even `key_x` constraint.
- The Hamming-weight oracle's purpose is only to cut the search space by a
  factor of 2 (parity filter); the diffuser is what actually amplifies the
  target keystate.
- VQF (QAOA-based) is included as a more NISQ-friendly alternative to QPE,
  since QPE's controlled-`U^(2^k)` circuits get very deep even for small
  `N`.
