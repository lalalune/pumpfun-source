#!/usr/bin/env python3
"""newcat.py <out.json>: catalog rows for this lane's captures built on main 1f4e396/5998913 (ev6+A6; admin_cto source
identical), with bytes/M against 2,251, where the byte delta lands relative to the new main, drift metrics, and the
splice of each with sh_iflet. Experiment only."""
import sys,os,json,subprocess
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import region,splice,genes_fk
from oracle import mask
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a02-cto-faithknobs')
NEWFB=O+'/rx/H_ev6_A6/fn.bin'; NEW=open(NEWFB,'rb').read(); main=open(O+'/rx/main/fn.bin','rb').read(); shif=open(O+'/rx/sh_iflet/fn.bin','rb').read()
rows=[]
for f in ('res-1f4e396.jsonl','res-5998913.jsonl'):
    p=f'{O}/{f}'
    if not os.path.exists(p): continue
    for l in open(p):
        r=json.loads(l); n=r['name']
        if 'error' in r: rows.append({'name':n,'genes':r.get('genes'),'error':r['error'][:200]}); continue
        if n.startswith('C'): continue          # C1-C4 were built from the 9bd38c7 source (genes include A6)
        fb=f'{O}/rx/{n}/fn.bin'
        if not os.path.exists(fb): continue
        x=open(fb,'rb').read(); s=splice.splice(main,[x,shif])
        d={'name':n,'genes':r.get('genes'),'bytes':len(x),'delta_bytes':len(x)-27400,'M':r['M'],'dM':r['M']-2251,
           'identical_to_base':mask(x)==mask(NEW),'by_region':region.regions(fb,NEWFB).get('by_region'),
           'with_sh_iflet':None if s is None else {'bytes':len(s),'M':splice.M(s)}}
        try: d['edit']=[{'old':e[0],'new':e[1]} for g in (r.get('genes') or '').split('+') if g in genes_fk.G for e in genes_fk.G[g] if not callable(e)]
        except Exception: pass
        q=subprocess.run(['python3',T+'/drift.py',fb],capture_output=True,text=True)
        try: d.update({k:v for k,v in json.loads(q.stdout.strip().splitlines()[-1]).items() if k in ('rfj_lcs','jumps_bad','jumps_aligned','drift_med')})
        except Exception: pass
        rows.append(d)
json.dump({'base':{'main':'1f4e396/5998913 (ev6+A6)','M':2251,'ratio':0.67436,'bytes':27400},'knobs':rows},open(sys.argv[1],'w'),indent=1)
print(len(rows))
