#!/usr/bin/env python3
# tab.py [ref=rar0] [w=1:2]: per trial dbytes, M, dM, masked M, frame-identity vs ref (share of aligned r10 offsets equal)
import json,os,re,subprocess,sys
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a08-cto-outlinefill'
ref=sys.argv[1] if len(sys.argv)>1 else 'rar0'; w=sys.argv[2] if len(sys.argv)>2 else '1:2'; wt=w.replace(':','')
def fnp(n): return f'{O}/bw/{n}_{wt}/fn.txt'
def M(n,r): k=sum(1 for _ in open(fnp(n))); return round(r*(3339+k)/2),k
rows={}
for l in open(O+'/res.jsonl'):
    r=json.loads(l)
    if isinstance(r.get(w),dict): rows[r['name']]=r
R=rows[ref][w]; Mr,_=M(ref,R['ratio'])
print(f"{'name':24s} {'bytes':>6s} {'dB':>5s} {'M':>5s} {'dM':>4s} {'Mmask':>5s} {'fz':>5s} genes")
for n,r in rows.items():
    x=r[w]; m,k=M(n,x['ratio']); mm=round(x['masked']*(3339+k)/2)
    o=subprocess.run(['python3',O+'/tools/offd.py',fnp(ref),fnp(n)],capture_output=True,text=True).stdout.split('\n')[0]
    h=dict((int(a),int(b)) for a,b in re.findall(r'\((-?\d+), (\d+)\)',o)); fz=h.get(0,0)/max(1,sum(h.values()))
    print(f"{n:24s} {x['bytes']:6d} {x['bytes']-R['bytes']:+5d} {m:5d} {m-Mr:+4d} {mm:5d} {fz:5.2f} {','.join(r['genes'])}")
