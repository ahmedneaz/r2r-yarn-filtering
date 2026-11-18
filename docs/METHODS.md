# Implemented filters and analysis methods

## Kalman filter

The state is `x = [omega_u, omega_r, T]^T`, measurement is `z = [omega_u_meas, omega_r_meas, T_raw]^T`, and input is `u = [tau_u, tau_r]^T`. Torque values come from the motor drivers.

The continuous matrices are

$$
A=\begin{bmatrix}-B_u/J_u&0&-r_u/J_u\\0&-B_r/J_r&r_r/J_r\\-k r_u&k r_r&0\end{bmatrix},\qquad
B=\begin{bmatrix}1/J_u&0\\0&1/J_r\\0&0\end{bmatrix},\qquad H=I_3.
$$

Forward Euler gives `F = I + A*Ts` and `Bd = B*Ts`. Prediction and correction follow the supplied code, with MATLAB right division for the gain, followed by covariance symmetrization. The initial state is the first measurement vector and `Pinit = diag(0.001, 0.001, 0.01)`. The first sample still executes prediction and correction after initialization.

| Parameter | Value | Declared unit / interpretation |
|---|---|---|
| `Ju` | 0.00793 | kg m² |
| `Bu` | 0.0101 | N m s/rad |
| `Jr` | 0.0043367 | kg m² |
| `Br` | 0.010292 | N m s/rad |
| `ru`, `rr` | 0.04, 0.05 | m |
| Primary `k_model` | 1.79 for both conditions | N/m in the supplied implementation; see provenance |
| `Qc` | diag(10, 10, 0.05) | Process-noise tuning matrix |
| `Rc` | diag(0.0001, 0.0001, 0.015) | Measurement-noise tuning matrix |
| `Qd` | `Qc * Ts` | First-order process-covariance approximation |
| `Rd` | `Rc / Ts` | Continuous measurement-intensity convention |
| At 1 kHz | `Qd = diag(0.01, 0.01, 0.00005)`; `Rd = diag(0.1, 0.1, 15)` | Implemented discrete matrices |

The tuning matrices have component-dependent state/measurement units; they are not independently calibrated physical noise measurements. The offline lower-stiffness replay changes only `k_model` to 0.37; it does not reidentify or optimize the entire KF.

## Scalar RLS

For `C = 1`, the supplied scalar recursion is

$$
g_k=\frac{P_{k-1}}{R+P_{k-1}},\qquad
\hat T_k=\hat T_{k-1}+g_k(T_{raw,k}-\hat T_{k-1}),\qquad
P_k=\frac{(1-g_k)P_{k-1}}{\lambda}.
$$

Nominal values are `lambda = 0.98`, `P0 = 100`, `R = 0.001`, and `x0 = 0`. Forgetting is applied after the measurement update, matching the supplied implementation. The gain approaches `1 - lambda = 0.02`. This is a scalar smoother with a deterministic gain trajectory for fixed parameters. There is no lattice stage or adjustable lattice order.

The steady recursion has transfer function `0.02 / (1 - 0.98 z^-1)`, low-frequency group delay 49 samples (49 ms at 1 kHz), and time constant approximately 49.5 ms. These are analytic response quantities, not measured computation times.

## Primary metrics

| Calculation | Definition |
|---|---|
| Startup exclusion | Use local `t >= 1 s` |
| Welch PSD | 1 kHz; Hann window; 4096 samples; 2048 overlap; constant detrend; one-sided density scaling |
| Band attenuation | `10*log10(input_band_power / output_band_power)` for 0.5–5, 5–50, and 50–450 Hz |
| Primary band integration | Trapezoidal integration over the existing Welch frequency bins inside each band |
| Raw power fractions | Interpolated boundaries at 0, 0.5, 5, 50, 450, 500 Hz; each band divided by total 0–500 Hz detrended Welch power |
| Trend proxy | Fourth-order, zero-phase Butterworth, 5 Hz; applied equally to the input and each output after startup exclusion |
| Trend deviation | Root mean square difference between filtered trends, in N; no amplitude alignment or time shifting |
| Trend correlation | Pearson correlation of the same trends |
| Lag proxy | Demeaned 5 Hz trends; full cross-correlation restricted to ±250 samples; positive lag means output follows input |
| Aggregation | Median, quartiles, and within-segment paired differences; no independent-run population p-values |

The per-band power fraction calculation intentionally interpolates band boundaries so that the five bands partition the spectrum. The primary attenuation calculation retains the original existing-bin rule. A median of per-segment powers is not the same as integrating the pointwise median PSD shown in a figure.

Higher-frequency power is not assumed to consist entirely of sensor noise. Trend deviation is agreement with a proxy derived from the recorded input, not error against an independent true-tension reference.

## Offline checks

| Check | Settings |
|---|---|
| Matched duration | `1 <= t <= 15 s` in every segment |
| Trend cutoff | 1, 2, 5, 10 Hz; with and without a further 1 s trim from each end of the smoothed interval |
| RLS forgetting factor | 0.90, 0.95, 0.98, 0.99, 0.995 |
| Initialization / weight | One factor at a time: `P0` = 0.001, 1, 100, 10000; `R` = 0.0001, 0.001, 0.01; `x0` = -0.2, 0, 0.2 |
| Butterworth baseline | Causal fourth-order filters at 2, 5, 10, 20 Hz; states initialized to the first input level |
| Scalar LMS baseline | Constant regressor 1; `x0 = 0`; update `x += mu*(measurement-x)`; steps 0.005, 0.01, 0.02, 0.05 |
| KF stiffness substitution | Lower-stiffness recordings only; `k_model = 0.37`; all other values and recorded inputs unchanged |

Baselines run from the beginning of a segment before the common first-second exclusion. The scalar LMS baseline is not a multi-tap noise canceller with a separate noise reference.

## Result files

| File in `results/reference/` | Contents |
|---|---|
| `record_manifest.csv` | Segment labels, sample counts, durations, raw-file hashes, and replay discrepancies |
| `primary_metrics.csv` | Primary stored RLS/KF metrics for every segment |
| `raw_band_power.csv` | Raw-signal power and percentage by frequency band |
| `equal_duration_metrics.csv` | Metrics for the common 1–15 s interval |
| `cutoff_sensitivity.csv` | Trend deviations and paired differences across cutoffs and edge treatments |
| `baseline_metrics.csv` | Butterworth and LMS metrics; LMS difference from RLS where applicable |
| `rls_sensitivity.csv` | Metrics for the forgetting-factor sweep |
| `initialization_sensitivity.csv` | Differences from nominal RLS during and after startup |
| `kf_stiffness_replay.csv` | Offline lower-stiffness KF coefficient substitution |
| `summary.json` | Group summaries, representative segment choices, software versions, verification, and operation counts |

Common metric columns are `low_db`, `mid_db`, `high_db`, `trend_rmse_n`, `trend_r`, `lag_ms`, `raw_high_rms_n`, and `output_high_rms_n`. Missing baseline-only diagnostics are blank for methods to which they do not apply. Per-segment identifiers remain distinct from sample counts.

## Figures

| Basename | Contents |
|---|---|
| `figure_2_design` | Fixed-calibration signal flow |
| `figure_3_algorithms` | KF and scalar RLS update sequences |
| `figure_4_traces` | Unshifted representative recorded traces, first 8 s |
| `figure_5_attenuation` | Median and IQR by frequency band |
| `figure_6_paired` | Per-segment RLS-minus-KF high-band attenuation |
| `figure_S1_psd` | Pointwise median spectra |
| `figure_S2_tradeoff` | Forgetting-factor and Butterworth attenuation/trend trade-offs |

The representative segments minimize the absolute difference between their paired high-band result and the group median: higher-stiffness Test 10 and lower-stiffness Test 1. Selection is algorithmic; all segments remain in the tabulated analysis.

## Computational counts

The algebraically reduced scalar RLS update uses two multiplications, four additions/subtractions, and two divisions, retaining two scalars. A three-state KF calculation exploiting `H = I` with otherwise dense products uses 114 multiplications and 114 additions/subtractions plus one 3 × 3 right-side solve, retaining three state values and nine covariance entries. These counts exclude initialization, constant-matrix construction, and arithmetic internal to the solve. They are not hardware execution-time benchmarks or the workload of every possible optimized implementation.
