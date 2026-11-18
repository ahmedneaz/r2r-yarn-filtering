# Data and code provenance

## Recordings

The authors designated the final supplied dataset as authoritative for this revision. The repository contains only those 40 segments and their 160 unchanged MAT files. Earlier arrangements and superseded channel assignments are not mixed into this release.

The authors report that the primary KF/RLS outputs were acquired online during real R2R operation using Simulink. They identify the torque inputs as motor-driver values, and the tension input as the load-cell channel. The files represent segments of continuous operation. The supplied folder numbering alone does not recover chronological adjacency or independent runs.

## Implementations

`KalmanFilterFunction.m` follows the latest supplied three-state KF equations and constants. The Python replay uses the same prediction and correction arithmetic with a transposed linear solve corresponding to MATLAB right division. Covariance/gain trajectories are cached in the Python implementation because they depend on the fixed matrices and initialization, not the measured innovation. This improves offline efficiency without changing the recursion.

`RecursiveLeastSquaresFunction.m` is a compact reproduction of the supplied scalar recursion, retaining the current estimate and covariance-like value instead of allocating an ever-growing history. It adds an explicit reset argument. These changes are packaging/implementation adaptations; they do not add a lattice predictor. The Python scalar recursion uses the same gain, estimate update, and post-update forgetting operation.

Both replay functions initialize at the start of every supplied segment. This initialization reproduces the stored outputs. Numerical correspondence does not by itself reconstruct the original Simulink execution history or demonstrate that the physical segments are independent.

## Additional analysis

The Python metric and plotting scripts were prepared for manuscript revision. Butterworth/LMS outputs, parameter sweeps, and stiffness substitution are computed offline from the existing recordings. The repository rearrangement adds directory input, a common entry point, integrity checks, and comparison to the preserved reference outputs. Numerical metric definitions are unchanged from the supplementary analysis package.

No acquisition `.slx` model, hardware timing log, independently calibrated clean-tension record, or new controlled-transition experiment is included. This is a data-and-analysis compendium, not a hardware deployment package.

## Physical parameter interpretation

The numerical stiffness constants are retained exactly as used in the supplied filter: 1.79 in the primary KF and 0.37 in the offline substitution. Their declared unit in the supplied model is N/m. A slope fitted directly against angle has units N/rad; conversion to linear stiffness requires the identification radius through `delta_x = r * delta_theta`. Numerical replay verifies the implemented constants, not that physical conversion. The manuscript identification figure and its conversion require author verification before release as definitive physical stiffness measurements.

## Preparation and validation

OpenAI ChatGPT assisted with organization, analysis-code preparation, and documentation. The authors remain responsible for review of the methods, code, data descriptions, and scientific interpretation. The package validation report records the checks actually executed. MATLAB code is supplied, but this preparation used Python for numerical verification; no MATLAB execution is claimed.

The original thesis identification image is not redrawn by this repository because its underlying identification measurements are not part of these 40 segments. All seven generated figures use Times New Roman; font files are not distributed.
