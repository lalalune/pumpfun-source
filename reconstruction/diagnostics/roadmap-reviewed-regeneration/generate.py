#!/usr/bin/env python3
"""Guard archived roadmap regeneration with a fixed reviewed-source digest."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = 'research/tooling-roadmap-call-classification-20261029/proof.py'
SOURCE = 'scripts/reconstruction_roadmap.py'
# Values come from reviewed repository assets, never the current input bytes.
REVIEWED = {
    SOURCE: 'e7f51159a9345abe7e7434ecda88346023446b47fc56aab01d0a2d1867b9603f',
    ARCHIVE: '8aeba2ad966d8540b1148d063f9c58cb89aa5ed45072c6433a7db7a4bdbe683d',
}


def admitted_inputs(root):
    bindings = {}
    for relative, expected in REVIEWED.items():
        raw = (root / relative).read_bytes()
        if hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest() != expected:
            raise ValueError(f'unreviewed source: {relative}')
        bindings[relative] = hashlib.sha256(raw).hexdigest()
    return bindings


def generate(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    bindings = admitted_inputs(root)  # Before loading or executing either module.
    if output.exists():
        raise ValueError('output already exists; retain prior results')
    spec = importlib.util.spec_from_file_location('reviewed_call_proof', root / ARCHIVE)
    proof = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(proof)
    report = proof.check(root)
    for name in proof.PROGRAMS:
        path = f'evidence/original/{name}/deployed.so'
        bindings[path] = hashlib.sha256((root / path).read_bytes()).hexdigest()
    output.mkdir(parents=True, exist_ok=False)
    (output / 'observations.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    (output / 'inputs.json').write_text(json.dumps(bindings, indent=2) + '\n', encoding='utf-8')
    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir())}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return report['totals']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(generate(args.repo, args.output), indent=2))
    except ValueError as error:
        parser.exit(1, str(error) + '\n')
