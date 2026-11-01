#!/usr/bin/env python3
"""tab.py: s3cashflag screen table (markdown) from rx/<c>/{res.json,mp.out}, fuev.jsonl, cm/<c>{,p2}.joint.json."""
import json,os,sys,hashlib
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a21-cto-s3cashflag/t2'); import disw as D
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a21-cto-s3cashflag'
F={}
if os.path.exists(O+'/fuev.jsonl'):
    for l in open(O+'/fuev.jsonl'):
        d=json.loads(l)
        v=sorted(int(x,16) for x in d['dot'].values() if x is not None); med=v[len(v)//2]; k=sum(1 for x in v if abs(x-med)>=0x800)
        d['swapc']='SWAP' if k>=3 else (f'{k} outlier' if k else 'no'); F[d['f'].split('/')[1]]=d
DESC={'m0':'main 5998913','S3n':'S3n (w16a08): hf out-param, curve store from hf, event holder.unwrap_or(false)',
 'c1':'cf:&mut bool per arm (false / st.cashback), head cashback removed, curve store from cf, event re-reads curve',
 'c2':'c1 + event reads cf','c3':'c1 + fee check (330) reads *cf','c4':'c3 + event reads cf',
 'c5':'cf written once at the end of validate (after the fee checks)','c6':'c5 + event reads cf',
 'c9':'no cf: execute derives !hf&&st.cashback after validate','c10':'c9 + event reads it',
 'c14':'per-arm cashback in execute\'s shared/holder arms (pa1 tuple) on S3','c14e':'c14 + event reads it',
 'c15':'holder arm clears st.cashback (&mut CtoState); fee check + curve store read st.cashback','c15e':'c15 + event reads it',
 'c16':'validate -> Result<(Pubkey,bool)> carries cashback (i1 SSA)','c16e':'c16 + event reads it',
 'c18':'cf written right after validate\'s cashback local (before fee checks)','c18e':'c18 + event reads it',
 'c19':'four arms in execute\'s block (non-shared split on holder)','c19e':'c19 + event reads it',
 'c5m':'LOO control: main (no S3) + c5\'s flag','c5g':'c5 + g1 (creator copy before validate)','c5F':'c5 + Fa (validate reads args.0)','c5gF':'c5 + g1 + Fa','c20g':'c20 + g1','c20F':'c20 + Fa','c20gF':'c20 + g1 + Fa',
 'c20':'per-arm cashback in execute\'s arms, non-shared arm reuses the head cashback (head kept)','c20e':'c20 + event reads it'}
FOLD={'c1':'c7, t1, t3, c11','c2':'c8, t2, t4, c12','c9':'c13','c10':'c13e'}
def shape(n):
    b=open(f'{O}/rx/{n}/fn.bin','rb').read(); L=D.d(b)
    for i,(o,t) in enumerate(L):
        if 'jeq r' in t and ', 2, ' in t and 0x4900<o<0x4c00:
            w=[t2 for _,t2 in L[i+2:i+6]]
            if 'and64' in w[1] and w[1].endswith(', 1') and 'ldxdw' in w[0]: return '1 load + and 1 (orig)'
            if 'and64' in w[2] and 'and64' in w[3]: return '2 loads + and + and 1 (main)'
            return 'load at store, no mask'
    return '?'
def joint(n,t=''):
    p=f'{O}/cm/{n}{t}.joint.json'
    if not os.path.exists(p): return ''
    try: return str(json.load(open(p))['Mhc'])
    except Exception: return ''
def forces(n,t=''):
    p=f'{O}/cm/{n}{t}.force'
    return len([x for x in open(p).read().strip().split(',') if x]) if os.path.exists(p) else ''
names=sys.argv[1:] or ['m0','S3n','c1','c2','c3','c4','c5','c6','c9','c10','c14','c14e','c15','c15e','c16','c16e','c18','c18e','c19','c19e','c20','c20e','c5m','c5g','c5F','c5gF','c20g','c20F','c20gF']
print('| cell | form | spellings folded | bytes | M | Mperm | Mhc | L--- | Lrfj | 6 KB swap | curve-store cashback | joint p1 (forces) | joint p2 (forces) |')
print('| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: |')
REF={'m0':('2251','2295','2302','2329 (7)','2339 (9)'),'S3n':('1990','2289','2296','2308 (7)','2347 (13)')}
for n in names:
    r=json.load(open(f'{O}/rx/{n}/res.json'))
    try: mp=json.loads(open(f'{O}/rx/{n}/mp.out').read().strip().splitlines()[-1])
    except Exception: mp={}
    f=F.get(n,{})
    if n in REF: M,Mp,Mh,j1,j2=REF[n]
    else:
        M,Mp,Mh=mp.get('M',''),mp.get('Mperm',''),mp.get('Mhc','')
        j1=joint(n); j1=f'{j1} ({forces(n)})' if j1 else ''
        j2=joint(n,'p2'); j2=f'{j2} ({forces(n,"p2")})' if j2 else ''
    print(f"| {n} | {DESC.get(n,'')} | {FOLD.get(n,'')} | {r['bytes']} | {M} | {Mp} | {Mh} | {f.get('L---','')} | {f.get('Lrfj','')} | {f.get('swapc','')} | {shape(n)} | {j1} | {j2} |")
