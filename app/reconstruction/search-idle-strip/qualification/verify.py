"""Read-only source/finite proof bindings; no provider or browser execution."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--dependency-root', type=Path, help='existing pinned app directory, read only; default: this tree app/')
args = parser.parse_args()
sha = lambda b: hashlib.sha256(b).hexdigest()

def check(base, row):
    p = Path(row['path'])
    assert not p.is_absolute() and '..' not in p.parts, row['path']
    b = (base / p).read_bytes()
    assert len(b) == row['bytes'] and sha(b) == row['sha256'], row['path']

manifest = json.loads((HERE / 'MANIFEST.json').read_text())
for row in manifest['files']:
    check(HERE, row)
inputs = json.loads((HERE / 'inputs.json').read_text())
for row in inputs['inputs']:
    check(ROOT, row)
receipt = json.loads((HERE / 'react-verification.json').read_text())
assert receipt['pass'] and not receipt['pageErrors'] and not receipt['unexpected']
assert len(receipt['observations']) == 17
assert len(receipt['bundledInputs']) == 15 and len(receipt['inputs']) == 7
expected_requests = [{'method': 'GET', 'path': '/'}, {'method': 'GET', 'path': '/fixture.js'}]
assert receipt['hostRequests'] == expected_requests

def runtime_inputs(r, historical=None):
    snapshots = {x['sourcePath'][4:]: x for x in historical or []}
    for row in r['bundledInputs'] + r['inputs']:
        if row['path'] in snapshots:
            snapshot = snapshots[row['path']]
            assert row['bytes'] == snapshot['bytes'] and row['sha256'] == snapshot['sha256']
            check(HERE, {**row, 'path': snapshot['packetPath']})
        else:
            base = args.dependency_root if row['path'].startswith('node_modules/') and args.dependency_root else ROOT / 'app'
            check(base, row)

runtime_inputs(receipt)
history = json.loads((HERE / 'historical-methods.json').read_text())
for method in history['methods']:
    r = json.loads((HERE / method['receipt']).read_text())
    assert not r.get('pass') and r['failure']
    assert not r['pageErrors'] and not r['unexpected'] and r['hostRequests'] == expected_requests
    for row in method['snapshots']:
        check(HERE, {**row, 'path': row['packetPath']})
    runtime_inputs(r, method['snapshots'])
argument = json.loads((HERE / 'argument-browser-failure.json').read_text())
repeat = json.loads((HERE / 'unchanged-browser-repeat.json').read_text())
assert argument['inputs'] == repeat['inputs'] and argument['bundledInputs'] == repeat['bundledInputs']
assert argument['bundleSha256'] == repeat['bundleSha256']
assert not repeat.get('pass') and repeat['failure']
runtime_inputs(repeat, history['methods'][1]['snapshots'])
assert len(argument['observations']) == len(repeat['observations']) == 2
assert len(json.loads((HERE / 'initial-browser-failure.json').read_text())['observations']) == 1
check(ROOT, {**history['unchangedClient'], 'bytes': (ROOT / history['unchangedClient']['path']).stat().st_size})
record = json.loads((HERE / 'work-record.json').read_text())
assert record['publicSourceHead'] == inputs['publicSourceRevision']
assert record['sourceTree'] == inputs['sourceTree']
assert record['inputBinding']['count'] == len(inputs['inputs'])
geometries = [o['geometry'] for o in receipt['observations']]
assert {'left': 360, 'width': 360, 'total': 1080} in geometries
assert {'left': 720, 'width': 360, 'total': 1080} in geometries
print(f"PASS {len(manifest['files'])} sealed members, {len(inputs['inputs'])} frozen Git inputs, 15 bundle/7 method inputs,17 final observations and3 historical failed receipts; no runtime replay or equivalence claim")
