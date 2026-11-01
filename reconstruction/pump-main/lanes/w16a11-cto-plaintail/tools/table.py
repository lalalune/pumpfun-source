#!/usr/bin/env python3
"""table.py: assemble the plaintail table (scr rows + fuev + lv + cells + lpipe joint) as markdown."""
import json,os,glob,subprocess,sys
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a11-cto-plaintail'); os.chdir(O)
rows={}
for f in glob.glob('res-*.jsonl'):
    for l in open(f):
        d=json.loads(l); rows[d['name']]=d
rows.setdefault('m0',{'name':'m0','genes':'-','bytes':27400,'M':2251,'Mperm':2295,'Mhc':2302})
fu={}
for l in open('data/fuev.jsonl'):
    d=json.loads(l); fu[d['f'].split('/')[1]]=d
ce={}
for l in open('data/cells.jsonl'):
    d=json.loads(l); ce[d['name']]=d
jo={}
for f in glob.glob('cm_*.pipe.log'):
    for l in open(f):
        if l.startswith('{"rx"'):
            d=json.loads(l); jo[d['rx']]=d
order=sys.argv[1:] or ['m0','R','P0','P0_S','P0_T','P0_C','P0_N','P0_R','P0_P','CNRP','RS','RT','RN','RC','RP','NRP','S1','SN','SC','SP','ST','Lv','LP0']
print('| variant | genes | bytes | M | Mperm | Mhc | true LCS --- | rfj | swap | free | +pin | +pin+ri9 (0x3c00) | +pin+ria (0x3c00) | +pin+ri9 (0x2800) | +pin+ria (0x2800) | joint (p1) |')
print('| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |')
for n in order:
    if n not in rows or 'error' in rows[n]: continue
    r=rows[n]; f=fu.get(n,{}); c=ce.get(n,{}); j=jo.get(n,{})
    print(f"| {n} | {r.get('genes')} | {r.get('bytes')} | {r.get('M')} | {r.get('Mperm')} | {r.get('Mhc')} | {f.get('L---','')} | {f.get('Lrfj','')} | {f.get('swap','')} | {c.get('free','')} | {c.get('pin','')} | {c.get('pin_ri9_0x3c00','')} | {c.get('pin_ria_0x3c00','')} | {c.get('pin_ri9_0x2800','')} | {c.get('pin_ria_0x2800','')} | {j.get('joint','')} |")
