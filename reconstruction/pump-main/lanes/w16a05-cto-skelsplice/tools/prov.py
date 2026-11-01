#!/usr/bin/env python3
"""prov.py <lane/rx/name or path>...: ledger provenance of an archived build (rows whose dedupe key or output names it)."""
import sys,os,json,re
L=os.path.expanduser('~/.cache/pumpfun-reconstruction/pump-main/ATTEMPTS.jsonl')
_rows=None
def rows():
    global _rows
    if _rows is None: _rows=[json.loads(l) for l in open(L) if l.strip()]
    return _rows
def lookup(p):
    p=p.replace(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/'),'')
    parts=p.split('/'); lane=parts[0]; name=parts[2] if len(parts)>2 and parts[1]=='rx' else parts[-2]
    out=[]
    for r in rows():
        if r.get('target')!='0x22a10': continue
        k=r.get('dedupe_key',''); o=str((r.get('data') or {}).get('output',''))
        if (r.get('lane')==lane or lane in o) and (k.endswith('-'+name+'-v1') or re.search(r'[-/]'+re.escape(name)+r'(-v\d+)?$',k) or o.rstrip('/').endswith('/'+name) or o.rstrip('/').endswith('/rx/'+name)):
            out.append(r)
    return lane,name,out
if __name__=='__main__':
    for p in sys.argv[1:]:
        lane,name,out=lookup(p)
        print(f'== {lane} {name}: {len(out)} rows')
        for r in out[-3:]:
            d=r.get('data') or {}
            print('  ',r.get('status'),r.get('approach'),r.get('dedupe_key'))
            print('     hyp:',str(r.get('hypothesis'))[:400])
            print('     note:',str(d.get('notes') or r.get('note') or '')[:300])
