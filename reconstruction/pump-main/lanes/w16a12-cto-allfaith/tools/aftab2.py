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
def stk(n,p='p0'):
    try: return json.load(open(f'{O}/stk/{n}_{p}/stk.json'))
    except Exception: return {}
def cells(n):
    try: return json.loads(open(f'{O}/g/{n}.cells.out').read().strip().splitlines()[-1])
    except Exception: return {}
RA={}
if os.path.exists(O+'/data/stkra.jsonl'):
    for l in open(O+'/data/stkra.jsonl'):
        r=json.loads(l); RA[r['n']]=r
m=R['m0']
order=sys.argv[1:] or sorted(R,key=lambda n:-(R[n].get('Mhc') or 0))
print('| cell | genes | bytes | M | dM | Mperm | Mhc | L--- | Lrfj | swap | restored stacked | pin | pin+ri9 | pin+ria | joint p1 (forces) |')
print('| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |')
for n in order:
    if n not in R: continue
    r=R[n]; s=stk(n); c=cells(n); a=RA.get(n,{})
    print(f"| {n} | {r['genes'][:48]} | {r['bytes']} | {r['M']} | {r['M']-m['M']:+d} | {r.get('Mperm','')} | {r.get('Mhc','')} | {r.get('lcs','')} | {r.get('Lrfj','')} | {r.get('swap','')} | "
          f"{s.get('stacked','')} | {c.get('pin','')} | {c.get('pin_ri9_0x3c00','')} | {c.get('pin_ria_0x3c00','')} | {str(a.get('stacked',''))+(' ('+str(a.get('nforce'))+')' if a else '')} |")
# ---- interaction table: I = d(HxT) - d(H) - d(T), d = metric - main's (stacked = restored+frame-normalised Mfnhc) ----
def met(n,k):
    if k=='stacked': return stk(n).get('stacked') or (2302 if n=='m0' else None)
    if k=='joint': return RA.get(n,{}).get('stacked')
    return R.get(n,{}).get(k)
pairs=[(h,h+'T') for h in ('h1','h1b','h2p','h2','h2f','h3','ft','h4','h3c','ftc') if h+'T' in R or h=='h4']
print('\n| H | metric | d(H) | d(T) | d(HxT) | I |')
print('| --- | --- | ---: | ---: | ---: | ---: |')
for h,ht in pairs:
    for k in ('M','Mhc','Lrfj','stacked','joint'):
        a,b,c,z=met(h,k),met('T',k),met(ht,k),met('m0',k)
        if None in (a,b,c,z): continue
        print(f'| {h} | {k} | {a-z:+d} | {b-z:+d} | {c-z:+d} | **{(c-z)-(a-z)-(b-z):+d}** |')
