# Reproducing the analysis

## 1. Python environment

The reference environment is Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0, and Matplotlib 3.10.8. The pinned dependency file captures those library versions. A CPU is sufficient; no GPU or MATLAB installation is needed for the Python pipeline.

Windows PowerShell, after opening the extracted repository folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe reproduce.py
```

Linux or macOS:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python reproduce.py
```

Activation is optional because these commands call the environment interpreter directly. Internet access is needed to install dependencies; after installation the analysis uses local files only.

## 2. Reproduction options

| Command | Work performed |
|---|---|
| `python reproduce.py --verify-only` | Check all file hashes, channel alignment, sampling, and KF/RLS replay |
| `python reproduce.py` | Verification, full numerical analysis, and comparison with reference results |
| `python reproduce.py --figures` | All of the above, followed by seven figures in PNG and PDF |

Use your virtual-environment interpreter in place of `python` when appropriate. Runtime depends on the computer. Each segment prints progress. The pipeline stops with an error if a required data file is missing, its checksum differs, replay fails, or numerical output disagrees with the reference beyond the documented tolerance.

Outputs are written to:

- `generated/verification.json`
- `generated/results/` (nine CSV tables, summary, and reference-comparison report)
- `generated/figures/` when `--figures` is requested

`generated/` is excluded by `.gitignore`; supplied reference outputs are in separate tracked folders. Re-running updates generated outputs only. A recorded replay match does not independently validate the source sensor connection or physical parameter units.

## 3. Figure fonts

All generated figure text uses Times New Roman. Matplotlib discovers a standard system installation. If it cannot find the font, set `R2R_FONT_DIR` to a directory containing your licensed Times New Roman TTF/OTF files. For example:

```powershell
$env:R2R_FONT_DIR = "C:\Windows\Fonts"
.\.venv\Scripts\python.exe reproduce.py --figures
```

```bash
R2R_FONT_DIR=/path/to/your/licensed/font/files .venv/bin/python reproduce.py --figures
```

The numerical pipeline works without the font. Font files are not bundled. Figure generation stops rather than silently substituting another family.

## 4. Individual Python commands

From the repository root:

```bash
python code/python/verify_data.py
python code/python/analyze.py data --out generated/results
python code/python/compare_results.py generated/results
python code/python/make_figures.py data --results generated/results --out generated/figures
```

The analysis and figure scripts also accept an archive containing the same two data groups. No re-zipping is required for the repository workflow. Retain the fixed 1 kHz sampling and complete Test_1–Test_20 structure when reproducing this specific study. Applying the methods to a different dataset requires a separately documented adaptation.

## 5. MATLAB replay and viewing

In MATLAB, change the current folder to the repository root, then run:

```matlab
addpath(fullfile(pwd,'code','matlab'));
verification = verify_recorded_outputs;
plot_recorded_segment('Soft_Yarn_Data',1);
plot_recorded_segment('Hard_Yarn_Data',10);
```

The replay function writes `generated/matlab/verification.csv`. Both filters reset at the first sample of each segment. The trace viewer plots the stored signals without additional filtering, time shifts, or amplitude changes. It requests Times New Roman for its labels.

These functions use ordinary MATLAB matrix operations and file loading; no Signal Processing Toolbox calls are used in this replay driver. The full spectral and sensitivity analysis is supplied in Python. MATLAB execution was not performed during package preparation; the recorded validation is from Python.

## 6. Interpreting verification

The data manifest checks exact file bytes. Replay checks all 40 segments with a maximum absolute tolerance of `1e-10` for each scalar stored state/output component; units follow the corresponding channel. The metric-comparison check uses relative tolerance `1e-7` and absolute tolerance `1e-8`, to allow small numerical differences across environments. Software version strings are reported but are not required to match in that numerical comparison.

The reference values are preserved in `results/reference/`. Differences should be investigated instead of replacing reference files with newly generated results merely to make the comparison pass.
