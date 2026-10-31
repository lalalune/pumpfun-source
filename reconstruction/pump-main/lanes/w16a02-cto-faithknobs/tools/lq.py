#!/usr/bin/env python3
"""lq.py <substr>...: fast in-memory ledger grep (0x22a10 rows whose JSON text contains every substring). Read-only."""
import sys,json,os
P=os.path.expanduser('~/.cache/pumpfun-reconstruction/pump-main/ATTEMPTS.jsonl')
rows=[l for l in open(P) if '0x22a10' in l]
for q in sys.argv[1:]:
    hits=[l for l in rows if q in l or q in l.replace('\\"','"')]
    print(f'== {q!r}: {len(hits)}')
    for l in hits[-4:]:
        d=json.loads(l); dd=d.get('data') or {}
        t=(dd.get('target') if isinstance(dd,dict) else None) or {}
        print('   ',d.get('timestamp_utc','')[5:16],d.get('lane','')[:22],d.get('status','')[:8],d.get('dedupe_key','')[-36:],json.dumps(t)[:110])
