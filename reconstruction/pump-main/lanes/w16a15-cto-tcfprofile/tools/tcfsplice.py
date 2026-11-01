#!/usr/bin/env python3
"""tcfsplice.py: transplant only the TCF-window hunks (main 0x2658..0x3b60) of a capture into main (splice oracle v2).
tcfx(raw) -> (spliced_raw | None, nhunks_in, nhunks_out). CLI: tcfsplice.py <out.jsonl> (scans an/scan_all.jsonl uniques)."""
import sys,os,json
from multiprocessing import Pool
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a15-cto-tcfprofile/reconstruction/pump-main/lanes/w16a15-cto-tcfprofile/tools')
import splice as S
from prof import rel
MAIN=open(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a15-cto-tcfprofile/an/main.bin'),'rb').read()
B=S.parse(MAIN); BT=S.targets(B)
off=[0]
for b in B: off.append(off[-1]+len(b))
LO=off.index(0x2658); HI=off.index(0x3b60)
def tcfx(raw,lo=LO,hi=HI):
    v=S.Var(B,raw); hin=[h for h in v.hunks if lo<=h[0] and h[1]<=hi]; hout=[h for h in v.hunks if h not in hin]
    if not hin: return None,0,len(hout)
    v.hunks=hin
    s=S.splice(MAIN,[v],B,BT)
    return s,len(hin),len(hout)
def ev(fb):
    try:
        raw=open(fb,'rb').read(); s,ni,no=tcfx(raw)
        if s is None: return {'fb':fb,'ni':ni,'no':no,'err':'none'}
        d,t,js=rel(s)
        return {'fb':fb,'ni':ni,'no':no,'bytes':len(s),'M':S.M(s),'good':sum(1 for x in d if x==0) if d else None,'cum':d}
    except Exception as e: return {'fb':fb,'err':repr(e)[:120]}
if __name__=='__main__':
    R=[json.loads(l) for l in open(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a15-cto-tcfprofile/an/scan_all.jsonl'))]
    seen={}; 
    for r in R:
        if 'th' in r and r['th'] not in seen: seen[r['th']]=r['fb']
    fs=sorted(seen.values()); print(len(fs),file=sys.stderr)
    with Pool(6) as p, open(sys.argv[1],'w') as f:
        for r in p.imap_unordered(ev,fs,chunksize=8): f.write(json.dumps(r)+'\n'); f.flush()
