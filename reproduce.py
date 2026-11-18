"""Repository entry point. Run with Python 3.12 after installing requirements.txt."""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CODE = ROOT / 'code/python'
GENERATED = ROOT / 'generated'


def run(script, *args):
    env = dict(os.environ)
    env.setdefault('MPLBACKEND', 'Agg')
    subprocess.run([sys.executable, str(CODE / script), *map(str, args)],
                   cwd=ROOT, env=env, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only', action='store_true', help='Check file hashes and replay outputs without the metric sweeps.')
    parser.add_argument('--figures', action='store_true', help='Also redraw figures; requires locally installed Times New Roman.')
    args = parser.parse_args()
    if args.verify_only and args.figures:
        parser.error('--verify-only and --figures cannot be combined.')
    GENERATED.mkdir(exist_ok=True)
    run('verify_data.py', '--out', GENERATED / 'verification.json')
    if not args.verify_only:
        run('analyze.py', ROOT / 'data', '--out', GENERATED / 'results')
        run('compare_results.py', GENERATED / 'results')
        if args.figures:
            run('make_figures.py', ROOT / 'data', '--results', GENERATED / 'results', '--out', GENERATED / 'figures')
    print(f'Completed. Generated files are in {GENERATED}')


if __name__ == '__main__':
    main()
