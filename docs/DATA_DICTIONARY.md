# Data dictionary

## Organization

Each of `data/Hard_Yarn_Data/` and `data/Soft_Yarn_Data/` contains `Test_1` through `Test_20`. These names identify supplied segments within a condition; they do not establish randomized order or statistical independence. The files come from continuous physical operation. A global time axis, gaps between segments, and original acquisition timestamps are not supplied, so concatenation into an uninterrupted experimental record is not justified.

Each segment has the four files below. The `.mat` files are read directly with MATLAB `load` or SciPy `loadmat`. Signal vectors may load with row or column orientation in MATLAB; use `(:)` for vector comparisons. Python uses `simplify_cells=True`, giving one-dimensional vectors.

| File | Variable | Meaning | Unit / shape |
|---|---|---|---|
| `raw.mat` | `t` | Local segment time | s; N samples |
| `raw.mat` | `T_raw` | Recorded load-cell tension input, as identified by the authors | N; N samples |
| `sensor.mat` | `t`, `T_raw` | Copies of the time and recorded tension input | Same as `raw.mat` |
| `sensor.mat` | `Ts` | Sampling period used in the KF | s; scalar, approximately 0.001 |
| `sensor.mat` | `omega_u_meas` | Unwinder encoder angular velocity | rad/s; N samples |
| `sensor.mat` | `omega_r_meas` | Rewinder encoder angular velocity | rad/s; N samples |
| `sensor.mat` | `tau_u` | Unwinder motor-driver torque value | N m; N samples |
| `sensor.mat` | `tau_r` | Rewinder motor-driver torque value | N m; N samples |
| `sensor.mat` | `yarn_type` | Supplied yarn-condition label | Text |
| `raw_vs_kalman.mat` | `t`, `T_raw` | Copies of time and the input tension | Same as `raw.mat` |
| `raw_vs_kalman.mat` | `T_kalman` | Stored online KF tension estimate | N; N samples |
| `raw_vs_kalman.mat` | `x_hat_kalman` | Stored posterior states: unwinder speed, rewinder speed, tension | 3 × N; rad/s, rad/s, N |
| `raw_vs_rls.mat` | `t`, `T_raw` | Copies of time and the input tension | Same as `raw.mat` |
| `raw_vs_rls.mat` | `T_rls` | Stored online scalar RLS tension estimate | N; N samples |

Here N means the number of samples; the same letter in the unit column denotes newtons when attached to force/tension. `results/reference/record_manifest.csv` gives the sample count and duration for every segment.

The torque channels are values reported by the two motor drivers. They are not reconstructed from the tension trace in this analysis, and are not independent torque-transducer measurements.

## Integrity and alignment

`metadata/data_file_hashes.json` lists the relative path, SHA-256 digest, and byte size of every MAT file. The verification script requires all 160 files, checks all hashes, confirms equality of duplicated time/tension vectors, checks finite values and 1 kHz time increments, and compares replayed outputs against the stored KF and RLS outputs.

Do not modify the files in `data/` to save newly calculated filters. Generated outputs belong in `generated/`. File integrity establishes identity to the supplied release, not independently calibrated sensor accuracy.

## Small loading examples

Python, from the repository root:

```python
from scipy.io import loadmat
d = loadmat("data/Soft_Yarn_Data/Test_1/raw.mat", simplify_cells=True)
t, recorded_tension = d["t"], d["T_raw"]
```

MATLAB, from the repository root:

```matlab
d = load(fullfile('data','Soft_Yarn_Data','Test_1','raw.mat'));
t = d.t(:);
recorded_tension = d.T_raw(:);
```
