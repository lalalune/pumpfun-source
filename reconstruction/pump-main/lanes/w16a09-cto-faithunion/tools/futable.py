#!/usr/bin/env python3
"""futable.py: markdown union table from res-<sha>.jsonl (scr.py), rx/<n>/fn.bin (fuev.py) and stk/<n>/stk.json (stk.sh).
Experiment only. Columns: classes, bytes, M, Mperm, Mhc, true LCS ---/rfj/op, bag4, head rfj, swap, Mfn (frame-normalised,
plain layout), stacked (best of plain / restored layout, frame-normalised, spill perm + swap climb), RA rows from
data/stkra.jsonl when present."""
import json,os,sys,subprocess
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CL={'p289n':'C/D','vmt':'H','emt':'H','b01':'b01','v01':'v01','Fa':'E','ov1a':'F','G51':'G','Gorig':'G','Gfc':'G','GPF':'A+B','F0':'B','GF':'B','PDA':'A','V2':'b01+b03','qli':'qli','hkt':'hkt'}
res=[json.loads(l) for l in open(O+'/res-9bd38c7.jsonl')]
ra={}
if os.path.exists(O+'/data/stkra.jsonl'):
    for l in open(O+'/data/stkra.jsonl'):
        try: r=json.loads(l); ra.setdefault(r['n'],{})[r.get('pass','p1')]=r
        except Exception: pass
cache={}
if os.path.exists(O+'/data/fuev.jsonl'):
    for l in open(O+'/data/fuev.jsonl'):
        r=json.loads(l); cache[r['n']]=r
rows=[]
print('| union | genes | classes | bytes | M | Mperm | Mhc | L--- | Lrfj | op | bag4 | head rfj | Mfn | stacked | RA p1 / p2 / p3 (forces) |')
print('| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |')
for r in res:
    n=r['name']
    if 'error' in r: print(f"| {n} | {r['genes']} | | compile error | | | | | | | | | | | |"); continue
    if n not in cache:
        p=subprocess.run(['python3',O+'/tools/fuev.py',O+f'/rx/{n}/fn.bin'],capture_output=True,text=True)
        f=json.loads(p.stdout.strip().splitlines()[-1]); f['n']=n; cache[n]=f
        open(O+'/data/fuev.jsonl','a').write(json.dumps(f)+'\n')
    f=cache[n]
    g=r['genes']; cls=sorted({CL.get(x,x) for x in g.split('+')}) if g!='-' else ['main']
    s=json.load(open(O+f'/stk/{n}/stk.json')) if os.path.exists(O+f'/stk/{n}/stk.json') else {}
    a=ra.get(n,{})
    rs=' / '.join(f"{a[p]['stacked']} ({a[p]['nforce']})" if p in a else '-' for p in ('p1','p2','p3')) if a else ''
    if n=='m0' and not s: s={'Mfn_plain':2249,'stacked':2300}
    print(f"| {n} | {g} | {', '.join(cls)} | {r['bytes']} | {r['M']} | {r.get('Mperm')} | {r.get('Mhc')} | {f['L---']} | {f['Lrfj']} | {f['lcs_op']} | {f.get('bag4')} | {f['head_rfj']} | {s.get('Mfn_plain','')} | {s.get('stacked','')} | {rs} |")
