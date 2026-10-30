"""Extract only synthetic query inputs from the preserved historical reports."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
REVISION = 'b4448f7bc202063a711565b543ae4b49770def90'
SPECS = [
    ('quote-selector-differential.json.gz', 'quote-selector-cases.json.gz',
     '87bef5fc75feb370199107d6ebd575cb9944ec53',
     ['normal', 'stable', 'flat', 'exotic', 'is_pump_pool', 'market_cap', 'quote_hex']),
    ('fee-selector-differential.json', 'fee-selector-cases.json.gz',
     '3cfb71ce3f61faa4eb3d4c58b9864e87baf85003',
     ['tiers', 'stable_tiers', 'market_cap', 'trade_size', 'option_bool_hex']),
]
provenance = {'scope': 'Synthetic on-chain query inputs only; historical expected outcomes and native compiler results are not imported.',
              'source_revision': REVISION, 'files': {}}
for source, destination, blob, fields in SPECS:
    path = 'repro/experiments/' + source
    raw = subprocess.check_output(['git', 'show', REVISION + ':' + path], cwd=ROOT)
    assert hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == blob
    report = json.loads(gzip.decompress(raw) if source.endswith('.gz') else raw)
    original = ROOT / 'evidence/original/pump_fees/deployed.so'
    assert report['original_sha256'] == hashlib.sha256(original.read_bytes()).hexdigest()
    cases = [{field: row[field] for field in fields} for row in report['cases']]
    content = (json.dumps({'cases': cases}, separators=(',', ':')) + '\n').encode()
    stream = io.BytesIO()
    with gzip.GzipFile(filename='', mode='wb', fileobj=stream, mtime=0) as compressed:
        compressed.write(content)
    encoded = stream.getvalue()
    (HERE / destination).write_bytes(encoded)
    provenance['files'][destination] = {'source_path': path, 'source_blob': blob,
        'source_sha256': hashlib.sha256(raw).hexdigest(), 'original_sha256': report['original_sha256'],
        'case_count': len(cases), 'fields_preserved': fields,
        'input_payload_sha256': hashlib.sha256(content).hexdigest(),
        'fixture_sha256': hashlib.sha256(encoded).hexdigest()}
(HERE / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
print(json.dumps(provenance, indent=2))
