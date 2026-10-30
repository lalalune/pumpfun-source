"""Read-only identity-audit benchmark over retained captures; no program executes.

Run this script with --repo pointing to each checkout and compare result_sha256.
Local timing observations are not a CI threshold or a reconstruction score.
"""
import argparse
import cProfile
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--repeats', type=int, default=3)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error('--repeats must be positive')
    root = args.repo.resolve()
    scripts = root / 'scripts'
    sys.path.insert(0, str(scripts))
    spec = importlib.util.spec_from_file_location('benchmarked_identity_audit', scripts / 'reconstruction_identity_audit.py')
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    paths = sorted((root / 'evidence/original').glob('*/deployed.so'))
    paths += sorted((root / 'evidence/dependencies').glob('*/deployed.so'))
    if not paths:
        parser.error('no retained captures in the selected checkout')

    def measure():
        # Separate reads model the original/candidate buffers used by the CLI.
        return [audit.measure(path.read_bytes(), path.read_bytes()) for path in paths]

    samples = []
    expected = None
    for _ in range(args.repeats):
        started = time.perf_counter()
        report = measure()
        samples.append(time.perf_counter() - started)
        serialized = json.dumps(report, sort_keys=True).encode()
        if expected is not None and serialized != expected:
            raise ValueError('identity reports changed between repetitions')
        expected = serialized
    profiler = cProfile.Profile()
    profiler.runcall(measure)
    layout_calls = sum(entry.callcount for entry in profiler.getstats()
                       if getattr(entry.code, 'co_name', None) == 'elf_layout')
    print(json.dumps({
        'captures': [{'path': path.relative_to(root).as_posix(),
                      'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for path in paths],
        'reader_sha256': {name: hashlib.sha256((scripts / name).read_bytes()).hexdigest()
                          for name in ('reconstruction_identity_audit.py', 'analyze.py', 'compare.py')},
        'samples_seconds': samples, 'median_seconds': statistics.median(samples),
        'elf_layout_calls': layout_calls,
        'result_sha256': hashlib.sha256(expected).hexdigest(),
    }, indent=2))


if __name__ == '__main__':
    main()
