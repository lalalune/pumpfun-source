#!/usr/bin/env python3
"""Compile the current native walk and compare real signed captured-program runs."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--revision', help='Compile the six host sources from this Git revision')
args = parser.parse_args()
root = args.repo.resolve()
sys.path.insert(0, str(root / 'tests'))
import test_curve_walk_funding_captured as probe

for path, digest in probe.walk.base.ELF_SHA256.items():
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError('captured image differs: ' + str(path))
with tempfile.TemporaryDirectory(prefix='curve-funding-probe-') as directory:
    host = Path(directory) / 'host'
    source = probe.walk.HOST_SOURCE
    if args.revision:
        sources = Path(directory) / 'recovered'
        sources.mkdir()
        for name in ('curve_walk_host.rs', 'curve_walk.rs', 'constant_product.rs',
                     'creator_fee_collect.rs', 'legacy_buy.rs', 'legacy_sell.rs'):
            data = subprocess.check_output(
                ['git', 'show', args.revision + ':programs/pump/recovered/' + name], cwd=root)
            (sources / name).write_bytes(data)
        source = sources / source.name
    subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings',
                    str(source), '-o', str(host)], check=True)
    rows = [probe.compare_case(host, case) for case in probe.scenarios()]
    result = {
        'base': '9120883a957d7d9b2cab6140f66fb5bc9e6774d5',
        'model_revision': args.revision or 'working-tree',
        'model_sha256': hashlib.sha256(
            source.with_name('curve_walk.rs').read_bytes()).hexdigest(),
        'compiler': subprocess.check_output(['rustc', '--version'], text=True).strip(),
        'host_sha256': hashlib.sha256(host.read_bytes()).hexdigest(),
        'cases': len(rows), 'steps': sum(len(row['captured']) for row in rows),
        'mismatched_cases': sum(not row['matches'] for row in rows),
        'mismatched_steps': sum(a != b for row in rows
                                for a, b in zip(row['captured'], row['host'])),
        'results': rows,
    }
with args.output.open('x', encoding='utf-8', newline='\n') as output:
    json.dump(result, output, indent=2)
    output.write('\n')
print(json.dumps({key: value for key, value in result.items() if key != 'results'}))
