#!/usr/bin/env python3
"""aftab2.py: markdown HxT table for NOTES (experiment only). Merges per cell:
res-<sha>.jsonl (bytes, M, Mperm, Mhc, true LCS ---/rfj, dotmap swap), stk/<n>_p0/stk.json (layout restored to main +
frame-normalised + spill perm, unforced), g/<n>.cells.out (w15a06 legal pin, pin+regideal r9 / all over 0x3c00-0x5040),
data/stkra.jsonl (pass-1 RA forces + restore + frame + perm = restored joint ceiling)."""
import json,os,glob,sys
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R={}
for f in glob.glob(O+'/res-*.jsonl'):
    for l in open(f):
        r=json.loads(l)
        if 'M' in r: R[r['name']]=r
R.setdefault('m0',{'name':'m0','genes':'- (main 1f4e396/5998913)','bytes':27400,'M':2251,'Mperm':2295,'Mhc':2302,'lcs':2257,'Lrfj':3006,'swap':False})
def swap6k(r):
    d=r.get('dot') or {}
    v=[int(x,16) for x in d.values() if x is not None]
    if not v: return 'no' if r.get('name')=='m0' else ''
    v.sort(); med=v[len(v)//2]
    k=sum(1 for x in v if abs(x-med)>=0x800)
    return 'SWAP' if k>=3 else (f'{k} outlier' if k else 'no')
def stk(n,p='p0'):
    try: return json.load(open(f'{O}/stk/{n}_{p}/stk.json'))
    except Exception: return {}
def cells(n):
    try: return json.loads(open(f'{O}/g/{n}.cells.out').read().strip().splitlines()[-1])
    except Exception: return {}
RA={};RA2={}
if os.path.exists(O+'/data/stkra.jsonl'):
    for l in open(O+'/data/stkra.jsonl'):
        r=json.loads(l)
        (RA2 if r.get('pass')=='p2' else RA)[r['n']]=r
m=R['m0']
order=sys.argv[1:] or sorted(R,key=lambda n:-(R[n].get('Mhc') or 0))
print('| cell | genes | bytes | M | dM | Mperm | Mhc | L--- | Lrfj | 6 KB swap | restored stacked | pin | pin+ri9 | pin+ria | joint p1 (forces) | joint p2 (forces) |')
print('| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |')
for n in order:
    if n not in R: continue
    r=R[n]; s=stk(n); c=cells(n); a=RA.get(n,{}); a2=RA2.get(n,{})
    print(f"| {n} | {r['genes'][:48]} | {r['bytes']} | {r['M']} | {r['M']-m['M']:+d} | {r.get('Mperm','')} | {r.get('Mhc','')} | {r.get('lcs','')} | {r.get('Lrfj','')} | {swap6k(r)} | "
          f"{s.get('stacked','')} | {c.get('pin','')} | {c.get('pin_ri9_0x3c00','')} | {c.get('pin_ria_0x3c00','')} | {str(a.get('stacked',''))+(' ('+str(a.get('nforce'))+')' if a else '')} | {str(a2.get('stacked',''))+(' ('+str(a2.get('nforce'))+')' if a2 else '')} |")
# ---- interaction table: I = d(HxT) - d(H) - d(T), d = metric - main's (stacked = restored+frame-normalised Mfnhc) ----
def met(n,k):
    if k=='stacked': return stk(n).get('stacked') or (2302 if n=='m0' else None)
    if k=='joint': return RA.get(n,{}).get('stacked')
    return R.get(n,{}).get(k)
pairs=[(h,h+'T') for h in ('h1','h1b','h2p','h2','h2f','h3','ft','h4','h3c','ftc','S1','S2','e1','hc') if h+'T' in R]
print('\n| H | metric | d(H) | d(T) | d(HxT) | I |')
print('| --- | --- | ---: | ---: | ---: | ---: |')
for h,ht in pairs:
    for k in ('M','Mhc','Lrfj','stacked','joint'):
        a,b,c,z=met(h,k),met('T',k),met(ht,k),met('m0',k)
        if None in (a,b,c,z): continue
        print(f'| {h} | {k} | {a-z:+d} | {b-z:+d} | {c-z:+d} | **{(c-z)-(a-z)-(b-z):+d}** |')
