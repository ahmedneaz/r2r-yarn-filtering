"""Check file integrity, signal alignment, and replay against stored outputs."""
import argparse
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import scipy
from analyze import load_records, rls, kalman

ROOT = Path(__file__).resolve().parents[2]


def verify():
    manifest = json.loads((ROOT / 'metadata/data_file_hashes.json').read_text())
    actual = {p.relative_to(ROOT).as_posix() for p in (ROOT / 'data').rglob('*.mat')}
    expected = {r['path'] for r in manifest}
    if len(manifest) != 160 or actual != expected:
        raise ValueError('The data tree does not match the 160-file manifest.')
    for item in manifest:
        content = (ROOT / item['path']).read_bytes()
        if len(content) != item['bytes'] or hashlib.sha256(content).hexdigest() != item['sha256']:
            raise ValueError(f"Data integrity check failed: {item['path']}")
    records = []
    for group, test, (raw, sensor, kf, rl), _ in load_records(ROOT / 'data'):
        t, tension = raw['t'], raw['T_raw']
        n = len(t)
        if t.ndim != 1 or tension.shape != (n,) or n < 15001:
            raise ValueError(f'Unexpected signal shape: {group}, Test {test}')
        for other in (sensor, kf, rl):
            if not np.array_equal(t, other['t']) or not np.array_equal(tension, other['T_raw']):
                raise ValueError(f'Time/tension copies differ: {group}, Test {test}')
        channels = [t, tension, kf['T_kalman'], rl['T_rls']]
        channels.extend(sensor[name] for name in ('omega_u_meas', 'omega_r_meas', 'tau_u', 'tau_r'))
        if any(np.shape(v) != (n,) or not np.all(np.isfinite(v)) for v in channels):
            raise ValueError(f'Nonfinite or mismatched channel: {group}, Test {test}')
        if not np.allclose(np.diff(t), .001, atol=1e-10, rtol=0) or not np.isclose(float(sensor['Ts']), .001, atol=1e-10, rtol=0):
            raise ValueError(f'Expected 1 kHz sampling: {group}, Test {test}')
        if np.shape(kf['x_hat_kalman']) != (3, n) or not np.all(np.isfinite(kf['x_hat_kalman'])):
            raise ValueError(f'Invalid saved KF states: {group}, Test {test}')
        y_rls = rls(tension)
        x_kf = kalman(sensor)
        rls_error = float(np.max(np.abs(y_rls - rl['T_rls'])))
        kf_error = float(np.max(np.abs(x_kf[:, 2] - kf['T_kalman'])))
        state_error = float(np.max(np.abs(x_kf.T - kf['x_hat_kalman'])))
        if max(rls_error, kf_error, state_error) > 1e-10:
            raise ValueError(f'Replay exceeds the numerical tolerance: {group}, Test {test}')
        records.append(dict(yarn=group, test=test, samples=n, rls_max_abs_error_n=rls_error,
                            kf_tension_max_abs_error_n=kf_error, kf_state_max_abs_error=state_error))
        print(f'Verified {group}, Test {test}', flush=True)
    return {'status': 'passed', 'data_files': len(manifest), 'segments': len(records),
            'versions': {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__},
            'scope': 'Byte integrity and numerical replay. This does not independently establish sensor wiring, physical stiffness units, or acquisition timing.',
            'records': records}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'generated/verification.json')
    args = parser.parse_args()
    result = verify()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(f"Passed: {result['data_files']} files; {result['segments']} segments. Report: {args.out}")
