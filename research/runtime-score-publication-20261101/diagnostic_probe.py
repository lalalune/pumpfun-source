#!/usr/bin/env python3
"""Actual control-flow/metric CLI report publication from retained ELF inputs."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import tempfile

SYMBOLS = 'research/pump-multihop-sell-fees-20261029/build/candidate/symbols.so.gz'
PROGRAM = 'evidence/original/pump/deployed.so'
TOOLS = {
    'control_flow': ['--start', '288', '--size', '176'],
    'target_metric': ['288', '--sym', 'h005e9f4277ff6fadE$'],
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(repo, revision=None):
    def limited():
        signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
        resource.setrlimit(resource.RLIMIT_FSIZE, (64, 64))

    repo = Path(repo).resolve()
    harness = repo / 'reconstruction/harness'
    inputs = {PROGRAM: (repo / PROGRAM).read_bytes(), SYMBOLS: (repo / SYMBOLS).read_bytes()}
    symbols = gzip.decompress(inputs[SYMBOLS])
    reports = {}
    for tool, options in TOOLS.items():
        relative = f'reconstruction/harness/{tool}.py'
        source = (subprocess.check_output(['git', '-C', str(repo), 'show', f'{revision}:{relative}'])
                  if revision else (repo / relative).read_bytes())
        with tempfile.TemporaryDirectory(prefix='diagnostic-publication-') as temporary:
            root = Path(temporary)
            cli = root / f'{tool}.py'
            cli.write_bytes(source)
            image = root / 'input.so'
            image.write_bytes(inputs[PROGRAM] if tool == 'control_flow' else symbols)
            outputs = root / 'reports'
            outputs.mkdir()
            environment = dict(os.environ, PYTHONPATH=str(harness))

            def invoke(output, limit=False):
                child = subprocess.run(
                    [sys.executable, '-B', str(cli), str(image), *options, '--json', str(output)],
                    env=environment, capture_output=True, text=True,
                    preexec_fn=limited if limit else None)
                blob = output.read_bytes() if output.exists() else None
                return {'exit': child.returncode,
                        'stderr': child.stderr.replace(str(root), '${TMP}'),
                        'stdout_sha256': digest(child.stdout.encode()),
                        'output_bytes': len(blob) if blob is not None else None,
                        'output_sha256': digest(blob) if blob is not None else None,
                        'files': sorted(path.name for path in outputs.iterdir())}

            output = outputs / 'report.json'
            limited_result = invoke(output, True)
            retry = invoke(output)
            control = invoke(outputs / 'control.json')
            prior = outputs / 'prior.json'
            prior.write_bytes(b'{"previous": "complete"}\n')
            existing = invoke(prior)
            existing['unchanged'] = prior.read_bytes() == b'{"previous": "complete"}\n'
            before_image = digest(image.read_bytes())
            alias = invoke(image)
            alias['unchanged'] = digest(image.read_bytes()) == before_image
            reports[tool] = {'cli_sha256': digest(source),
                             'publisher_sha256': (digest((harness / 'compare_scores.py').read_bytes())
                                                   if b'from compare_scores import publish_report' in source else None),
                             'arguments': options,
                             'image_sha256': before_image, 'limited_write': limited_result,
                             'same_command_retry': retry, 'unlimited_control': control,
                             'existing_output': existing, 'image_alias': alias}
    return {'revision': revision or 'working tree',
            'input_sha256': {name: digest(blob) for name, blob in inputs.items()},
            'symbols_elf_sha256': digest(symbols),
            'harness_support_sha256': {name: digest((harness / name).read_bytes()) for name in
                                       ('score.py', 'score_admission.py', 'instruction_stream.py',
                                        'elf_symbols.py', 'win.py', 'original_input.py')},
            'inventory_sha256': digest((repo / 'reconstruction/base/functions.tsv').read_bytes()),
            'reports': reports,
            'inputs_unchanged': all((repo / name).read_bytes() == blob for name, blob in inputs.items()),
            'limits': 'Actual POSIX diagnostic CLIs reading retained ELF bytes; no compiler, VM, new match or acceptance-score claim. --revision replaces only the CLI; unchanged local harness dependencies are hashed.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', type=Path)
    parser.add_argument('--revision')
    args = parser.parse_args()
    print(json.dumps(run(args.repo, args.revision), indent=2))
