#!/usr/bin/env python3
"""Replay the packet verifier and refusal controls with supplied pinned ELF builds."""
import argparse
import gzip
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('repo', 'baseline', 'candidate'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    repo, baseline, candidate = (getattr(args, name).resolve()
                                 for name in ('repo', 'baseline', 'candidate'))
    checks = []
    with tempfile.TemporaryDirectory(prefix='pump-five-verifier-') as temporary:
        root = Path(temporary)

        def exercise(name, flags=(), mutate=None, wrong=False, existing=False):
            packet = root / name / 'packet'
            shutil.copytree(HERE, packet, ignore=shutil.ignore_patterns('__pycache__'))
            if mutate:
                mutate(packet)
            output = root / name / 'report.json'
            if existing:
                output.write_bytes(b'preserve existing report\n')
            command = [sys.executable, *flags, '-B', str(packet / 'verify.py'),
                       '--repo', str(repo), '--baseline', str(baseline),
                       '--candidate', str(baseline if wrong else candidate),
                       '--report', str(output)]
            result = subprocess.run(command, capture_output=True, text=True, timeout=120)
            rejected = mutate is not None or wrong or existing
            require((result.returncode != 0) == rejected,
                    name + ': unexpected status\n' + result.stdout + result.stderr)
            if existing:
                require(output.read_bytes() == b'preserve existing report\n',
                        name + ': existing report changed')
            elif rejected:
                require(not output.exists(), name + ': refused input published a report')
            else:
                report = json.loads(output.read_text())
                require(report['verified'] is True and not any(report['losses'].values()),
                        name + ': invalid success report')
            checks.append({'case': name, 'passed': True})

        exercise('normal')
        exercise('optimized', ('-O',))
        exercise('docstring-optimized', ('-OO',))
        exercise('wrong-candidate', wrong=True)
        exercise('existing-output', existing=True)

        def change_census(packet):
            path = packet / 'candidate-score.json.gz'
            value = json.loads(gzip.decompress(path.read_bytes()))
            first = next(iter(value['windows'].values()))
            first['normalized'] = not first['normalized']
            path.write_bytes(gzip.compress(json.dumps(value).encode(), mtime=0))

        exercise('changed-census', mutate=change_census)

        def change_source(packet):
            path = packet / 'candidate-source.json'
            value = json.loads(path.read_text())
            value['sha256'] = '0' * 64
            path.write_text(json.dumps(value))

        exercise('changed-source-binding', mutate=change_source)
    print(json.dumps({'checks': checks, 'compiler_or_runtime_executions': 0}, indent=2))


if __name__ == '__main__':
    main()
