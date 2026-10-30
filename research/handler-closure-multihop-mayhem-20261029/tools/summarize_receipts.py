import gzip
import json
import sys
from pathlib import Path

for arg in sys.argv[1:]:
    p = Path(arg)
    raw = p.read_bytes()
    d = json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)
    summary = {k: d[k] for k in ('case_count', 'original_successes', 'original_pump_cpi_cases',
                                 'verified_outer_signatures', 'mismatches') if k in d}
    summary['file'] = p.name
    if 'cases' in d:
        per = []
        for row in d['cases']:
            o = row.get('original', {})
            per.append({'case': row.get('case') or row.get('case', {}).get('case'),
                        'original_error': o.get('error'),
                        'pump_calls': len(o.get('pump_calls', [])) if 'pump_calls' in o else None,
                        'mismatches': row.get('mismatches', row.get('diff'))})
        summary['per_case'] = per
    print(json.dumps(summary, indent=1)[:4000])
