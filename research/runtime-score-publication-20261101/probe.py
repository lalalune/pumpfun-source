#!/usr/bin/env python3
"""Exercise actual score comparison publication; no program execution or mocks."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import signal
import subprocess
import sys
import tempfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repository', type=Path)
    parser.add_argument('--revision', help='run the standalone CLI from this git revision')
    args = parser.parse_args()
    repository = args.repository.resolve()
    relative = 'reconstruction/harness/compare_scores.py'
    inputs = [repository / 'reconstruction/pump-main/baseline' / name
              for name in ('score.json', 'rescore.json')]
    source = (subprocess.check_output(['git', '-C', str(repository), 'show',
                                     f'{args.revision}:{relative}'])
              if args.revision else (repository / relative).read_bytes())

    def limited():
        signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
        resource.setrlimit(resource.RLIMIT_FSIZE, (64, 64))

    with tempfile.TemporaryDirectory(prefix='score-publication-proof-') as temporary:
        root = Path(temporary)
        cli = root / 'compare_scores.py'
        cli.write_bytes(source)
        reports = root / 'reports'
        reports.mkdir()

        def run(output, limit=False):
            result = subprocess.run(
                [sys.executable, '-B', str(cli), *(str(path) for path in inputs),
                 '--json', str(output)], capture_output=True, text=True,
                preexec_fn=limited if limit else None)
            return {'exit': result.returncode,
                    'stderr': result.stderr.replace(str(root), '${TMP}'),
                    'stdout': result.stdout,
                    'report_exists': output.exists(),
                    'report_bytes': output.stat().st_size if output.exists() else None,
                    'files': sorted(path.name for path in reports.iterdir())}

        before = {str(path.relative_to(repository)): digest(path) for path in inputs}
        output = reports / 'comparison.json'
        failed = run(output, limit=True)
        retry = run(output)
        control = run(reports / 'control.json')
        existing_path = reports / 'existing.json'
        existing_path.write_bytes(b'{"prior": "complete"}\n')
        existing_before = digest(existing_path)
        existing = run(existing_path)
        existing['unchanged'] = digest(existing_path) == existing_before
        # Existing-input refusals do not write either retained report.
        aliases = [run(path) for path in inputs]
        print(json.dumps({
            'source_revision': args.revision or 'working tree',
            'source_sha256': hashlib.sha256(source).hexdigest(),
            'method': 'actual standalone CLI with retained score/rescore JSON; child RLIMIT_FSIZE=64',
            'input_sha256': before,
            'input_window_counts': [len(json.loads(path.read_text())['windows']) for path in inputs],
            'failed_write': failed, 'same_command_retry': retry,
            'unlimited_control': control, 'existing_report': existing,
            'input_aliases': aliases,
            'inputs_unchanged': before == {str(path.relative_to(repository)): digest(path) for path in inputs},
            'limits': 'POSIX filesystem failure reproduction; no build, scorer rerun, VM or program execution',
        }, indent=2))


if __name__ == '__main__':
    main()
