# R2R yarn tension filtering: data and reproducible analysis

Companion research materials for **Data-Driven RLS Filtering for Adaptive Noise Reduction in Roll-to-Roll Systems: A Paired Comparison across Yarn Stiffness Conditions** (Machines manuscript **machines-4670088**).

**Authors:** Ahmed Neaz, Eunha Lee, Byeongil Kim, and Kanghyun Nam.

This repository contains the supplied recordings, MATLAB filter implementations, Python analysis, numerical reference results, and publication figures. Both filters were calibrated using the higher-stiffness yarn and retained for the lower-stiffness condition. The comparison examines retention of fixed settings across these two conditions.

## Data at a glance

| Item | Contents |
|---|---|
| Yarn conditions | Higher stiffness (`Hard_Yarn_Data`) and lower stiffness (`Soft_Yarn_Data`) |
| Recorded segments | 20 per condition; 40 in total |
| Sampling | 1 kHz; 1 ms sample interval |
| Durations | Higher stiffness: 15–30 s; lower stiffness: 20–30 s |
| Files | Four MAT files per segment; 160 MAT files in total |
| Signals | Recorded tension, both encoder speeds, both motor-driver torque values, and stored KF/RLS outputs |
| Experimental origin | Online physical R2R operation recorded through Simulink, as reported by the authors |
| Statistical unit | Paired segment; segments of continuous operation are not independent experimental repetitions |

The data files are unchanged copies of the final author-supplied dataset. The channel `T_raw` is the recorded tension input as identified by the authors. Numerical verification checks file integrity, alignment, and correspondence between the recursions and the stored outputs; it does not independently verify sensor wiring or the physical identification procedure.

## Quick start

Use **Python 3.12**. From this repository folder, install the supplied environment and run:

```bash
python -m pip install -r requirements.txt
python reproduce.py
```

The command checks all 160 data files, replays both filters, computes the primary comparisons and offline sensitivity analyses, and compares the regenerated results with the supplied numerical reference. New output goes to `generated/`; recordings and reference results remain unchanged.

For integrity and replay checks only:

```bash
python reproduce.py --verify-only
```

To also regenerate the seven figures:

```bash
python reproduce.py --figures
```

Figure generation requires **Times New Roman** installed locally. The numerical analysis does not require that font. Existing PNG and PDF figures are available in `figures/reference/`. See [reproduction instructions](docs/REPRODUCING.md) for Windows setup, MATLAB verification, and font configuration.

## Repository contents

| Path | Purpose |
|---|---|
| `data/Hard_Yarn_Data/Test_1` … `Test_20` | Higher-stiffness recordings |
| `data/Soft_Yarn_Data/Test_1` … `Test_20` | Lower-stiffness recordings |
| `code/matlab/` | KF and scalar RLS functions, replay verification, and a trace viewer |
| `code/python/` | Metrics, baseline comparisons, parameter checks, verification, and figure scripts |
| `results/reference/` | Nine per-segment CSV tables and `summary.json` from the revised analysis |
| `figures/reference/` | Five main figures and two supplementary figures, each as PNG and PDF |
| `metadata/` | File hashes, implemented parameters, and package validation report |
| `docs/` | Data dictionary, methods, reproduction, and provenance |
| `reproduce.py` | Single entry point for reproducing the analysis |
| `CITATION.cff` | Citation metadata for this research package |

## What the code implements

- **KF:** three states, `[omega_u, omega_r, T]`, encoder and tension measurements, motor-driver torque inputs, and forward Euler discretization. The supplied model coefficient remains 1.79 for both conditions. All constants, covariance settings, and initialization are documented in [METHODS.md](docs/METHODS.md).
- **RLS:** scalar constant-regressor recursion with `C = 1`, `lambda = 0.98`, `P0 = 100`, `R = 0.001`, and `x0 = 0`. It has no lattice stage or lattice-order parameter. The gain approaches 0.02.
- **Offline analyses:** causal Butterworth and scalar LMS baselines, RLS forgetting-factor and initialization sweeps, trend-cutoff checks, matched-duration comparisons, and a lower-stiffness KF coefficient substitution. These are replays of existing measurements, not additional physical experiments.

## Reading the results

The primary analysis excludes the first second of each segment. Positive band attenuation means lower output power relative to the recorded tension input. Trend deviation describes agreement with a low-pass trend derived from that same input. The cross-correlation lag is a waveform timing proxy, not a measurement of processor execution time.

The results concern the supplied configurations and trajectories. They do not establish a universal estimator ranking, performance for an untested catalogue of yarns, or absolute true-tension accuracy. The scalar LMS baseline closely matches nominal RLS after startup; a tested 20 Hz Butterworth baseline improves both high-band attenuation and trend deviation. All baseline settings and outputs are retained in the supplied results.

## Citation and reuse

Use [CITATION.cff](CITATION.cff) when citing this package and identify the version or commit used. The associated manuscript is identified above; no article DOI or publication status is asserted in this preparation package.

No reuse license has been selected in this package. The authors should add their chosen code and data licenses before advertising unrestricted reuse. Public availability and an open-source license are separate decisions.

## Documentation

- [Data dictionary](docs/DATA_DICTIONARY.md)
- [Analysis methods and result files](docs/METHODS.md)
- [Reproduction instructions](docs/REPRODUCING.md)
- [Data and code provenance](docs/PROVENANCE.md)

Numerical verification was run using Python. MATLAB functions are provided for independent reproduction; the package does not claim that MATLAB execution or a new Simulink hardware run was performed during repository preparation.
