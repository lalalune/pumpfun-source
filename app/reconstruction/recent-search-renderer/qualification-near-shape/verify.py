"""Read-only finite packet/source bindings; never runs captures or providers."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--dependency-root', type=Path, help='existing pinned app/node_modules parent, read only; default is this tree app/')
args = parser.parse_args()
sha = lambda b: hashlib.sha256(b).hexdigest()

def check(base, record):
    relative = Path(record['path'])
    assert not relative.is_absolute() and '..' not in relative.parts, record['path']
    data = (base / relative).read_bytes()
    assert len(data) == record['bytes'] and sha(data) == record['sha256'], record['path']

manifest = json.loads((HERE / 'MANIFEST.json').read_text())
for row in manifest['files']:
    check(HERE, row)
inputs = json.loads((HERE / 'inputs.json').read_text())
for row in inputs['inputs']:
    check(ROOT, row)
receipt = json.loads((HERE / 'react-verification.json').read_text())
assert receipt['pass'] and not receipt['pageErrors'] and not receipt['unexpected']
assert receipt['hostRequests'] == [{'method': 'GET', 'path': '/'}, {'method': 'GET', 'path': '/fixture.js'}]
assert len(receipt['observations']) == 17
assert len(receipt['bundledInputs']) == 15 and len(receipt['inputs']) == 7
for row in receipt['inputs']:
    check(ROOT / 'app', row)
for row in receipt['bundledInputs']:
    base = args.dependency_root if row['path'].startswith('node_modules/') and args.dependency_root else ROOT / 'app'
    check(base, row)
record = json.loads((HERE / 'work-record.json').read_text())
assert record['publicSourceHead'] == inputs['publicSourceRevision']
assert record['sourceTree'] == inputs['sourceTree']
assert record['inputBinding']['count'] == len(inputs['inputs'])
print(f"PASS {len(manifest['files'])} sealed members, {len(inputs['inputs'])} frozen source/evidence inputs, 15 bundle/7 method inputs and 17 finite React observations; no runtime replay or equivalence claim")

# A supplied Near helper shape correction is qualified separately from the first run.
history = json.loads((HERE / 'historical-preservation.json').read_text())
for row in history['preservedFiles']:
    check(ROOT, row)
assert len(history['preservedFiles']) == 14
assert sha((HERE / 'react-verification.json').read_bytes()) == history['correctedReceiptSHA256']
assert sha((ROOT / 'app/reconstruction/recent-search-renderer/client.mjs').read_bytes()) == history['controllerUnchangedSHA256']
rows = receipt['observations'][2]['records']['coinRows']
assert any(row['mint'] == 'synthetic.near' and row['chainId'] == 'near:mainnet' for row in rows)
print('PASS exact Near chainId handoff and all 14 historical packet files preserved; 17 repeated controls, not 34 unique cases')
