"""Read-only frozen source and finite read-workflow bindings; no providers run."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--dependency-root', type=Path, help='existing pinned app dependency directory, read-only')
args = parser.parse_args()

def check(base, row):
    p = Path(row['path'])
    assert not p.is_absolute() and '..' not in p.parts, row['path']
    data = (base / p).read_bytes()
    assert len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256'], row['path']

manifest = json.loads((HERE / 'MANIFEST.json').read_text())
for row in manifest['files']:
    check(HERE, row)
inputs = json.loads((HERE / 'inputs.json').read_text())
for row in inputs['inputs']:
    check(ROOT, row)
receipt = json.loads((HERE / 'read-verification.json').read_text())
assert receipt['pass'] and 'failure' not in receipt
assert len(receipt['observations']) == 14
assert len(receipt['requests']) == len(receipt['apiCalls']) == 13
assert all(r['method'] == 'GET' for r in receipt['requests'])
assert len(receipt['inputs']) == 7 and len(receipt['dependencies']) == 2
for row in receipt['inputs']:
    check(ROOT / 'app', row)
for row in receipt['dependencies']:
    check(args.dependency_root or ROOT / 'app', row)
record = json.loads((HERE / 'work-record.json').read_text())
assert record['publicSourceHead'] == inputs['publicSourceRevision']
assert record['sourceTree'] == inputs['sourceTree']
assert record['inputBinding']['count'] == len(inputs['inputs'])
contexts = {o['context'] for o in receipt['observations'] if 'context' in o}
assert len(contexts) == 5
print(f"PASS {len(manifest['files'])} sealed members, {len(inputs['inputs'])} frozen Git inputs,7method/2installed dependency files and14observations/13local GETs across5physical contexts; no runtime replay or endpoint/schema equivalence claim")
