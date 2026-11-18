"""Compare regenerated metrics with the supplied numerical reference results."""
import argparse
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def same_value(actual, expected, label):
    try:
        a, b = float(actual), float(expected)
    except (TypeError, ValueError):
        if actual != expected:
            raise ValueError(f'Mismatch at {label}: {actual!r} != {expected!r}')
    else:
        if not math.isclose(a, b, rel_tol=1e-7, abs_tol=1e-8):
            raise ValueError(f'Numerical mismatch at {label}: {a} != {b}')


def compare_json(actual, expected, label='summary'):
    if isinstance(expected, dict):
        if set(actual) != set(expected):
            raise ValueError(f'JSON keys differ: {label}')
        for key in expected:
            if key != 'versions':
                compare_json(actual[key], expected[key], f'{label}.{key}')
    elif isinstance(expected, list):
        if len(actual) != len(expected):
            raise ValueError(f'JSON list lengths differ: {label}')
        for i, (a, b) in enumerate(zip(actual, expected)):
            compare_json(a, b, f'{label}[{i}]')
    else:
        same_value(actual, expected, label)


def compare(results):
    reference = ROOT / 'results/reference'
    files = []
    for source in sorted(reference.glob('*.csv')):
        target = results / source.name
        with source.open(newline='', encoding='utf-8') as f:
            expected = list(csv.DictReader(f))
        with target.open(newline='', encoding='utf-8') as f:
            actual = list(csv.DictReader(f))
        if len(actual) != len(expected):
            raise ValueError(f'Row counts differ: {source.name}')
        for i, (a, b) in enumerate(zip(actual, expected), 2):
            if set(a) != set(b):
                raise ValueError(f'Column names differ: {source.name}')
            for key in b:
                same_value(a[key], b[key], f'{source.name}:{i}:{key}')
        files.append({'file': source.name, 'rows': len(actual)})
    compare_json(json.loads((results / 'summary.json').read_text()),
                 json.loads((reference / 'summary.json').read_text()))
    return {'status': 'passed', 'csv_files': files, 'summary_checked': True,
            'relative_tolerance': 1e-7, 'absolute_tolerance': 1e-8,
            'note': 'Software-version strings may differ. Replay has a separate stricter 1e-10 check.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', type=Path)
    args = parser.parse_args()
    result = compare(args.results)
    (args.results / 'comparison_to_reference.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('All nine result CSVs and the numerical summary agree with the reference package.')
