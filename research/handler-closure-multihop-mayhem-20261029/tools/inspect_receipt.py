"""Inspect saved multi_hop receipts: error + last logs per case, side by side."""
import gzip
import json
import sys
from pathlib import Path

p = Path(sys.argv[1])
raw = p.read_bytes()
data = json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)
want = sys.argv[2:] if len(sys.argv) > 2 else None
for row in data['cases']:
    if want and row['case'] not in want:
        continue
    o, c = row['original'], row['candidate']
    print('=' * 100)
    print(row['case'], 'mismatches=', row['mismatches'])
    for side, r in (('original', o), ('candidate', c)):
        print(f'--- {side}: error={r["error"]}')
        for line in r['logs']:
            print('   ', line)
        print('    events:', len(r['events']), 'pump_calls:', len(r['pump_calls']), 'token_calls:', len(r['token_calls']))
