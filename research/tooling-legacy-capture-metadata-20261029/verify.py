#!/usr/bin/env python3
"""Read-only verifier for the legacy capture metadata packet."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import proof

P = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo', type=Path, default='.')
args = parser.parse_args()
root = args.repo.resolve()
assert root == proof.REPO, (root, proof.REPO)
sha = lambda data: hashlib.sha256(data).hexdigest()

inventory = json.loads((P / 'manifest.json').read_text())
actual = {
    str(path.relative_to(P)): sha(path.read_bytes())
    for path in sorted(P.rglob('*'))
    if path.is_file() and path.name != 'manifest.json'
    and '__pycache__' not in path.parts and path.suffix != '.pyc'
}
assert actual == inventory, 'packet inventory differs'
inputs = json.loads((P / 'inputs.json').read_text())
for name, digest in inputs.items():
    assert sha((root / name).read_bytes()) == digest, name
report = proof.check(root)
saved = json.loads(gzip.decompress((P / 'observations.json.gz').read_bytes()))
assert report == saved, 'fresh observations differ'
delta = json.loads((P / 'coverage-delta.json').read_text())
assert delta['totals']['legacy_captures'] == report['legacy_captures']
print(json.dumps({
    'captures': len(report['captures']),
    'legacy': report['legacy_captures'],
    'upgradeable': report['upgradeable_captures'],
}, indent=2))
