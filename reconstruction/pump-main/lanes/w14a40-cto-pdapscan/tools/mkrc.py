#!/usr/bin/env python3
"""mkrc.py <base.py> <outdir> <log>...: for each scannable clone, a variant (on top of the accepted state) with its lamports/data Rc clones swapped."""
import sys,os,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import lab2src as L
base,od=sys.argv[1:3]; os.makedirs(od,exist_ok=True); acc={}
for lf in sys.argv[3:]:
    CC=L.C if lf.startswith('cd1/') else L.C1
    for l in open(lf):
        r=json.loads(l)
        if r.get('accepted'): acc[CC[r['clone']]]=r['best']['lab']
A=list(acc.items())
def swap(s,key):
    sg,pre,ac=key; i=s.index(L.MK[sg]); i=s.rindex('\n',0,i); j=s.index('\n',i+1); seg=s[i:j]
    a,b=L.span(seg,pre); e=seg[a:b]
    if e.endswith('.to_account_info()'): e=L.newlit(ac,'022222:key.owner.rent.f40.f41.f42',e)
    F=L.fields(e); import re
    m=re.search(r'AccountInfo\{(.*)\}\}$',e); parts=re.split(r',(?=[a-z_]+:)',m.group(1))
    il=[k for k,p in enumerate(parts) if p.startswith('lamports:')][0]; idd=[k for k,p in enumerate(parts) if p.startswith('data:')][0]
    parts[il],parts[idd]=parts[idd],parts[il]
    e=e[:m.start(1)]+','.join(parts)+e[m.end(1):]
    return s[:i]+seg[:a]+e+seg[b:]+s[j:]
for k in L.C1.values():
    n='rc_'+k[0]+'_'+k[1].strip(':(').replace('::','_').replace('(','')
    open(f'{od}/{n}.py','w').write(open(base).read()+'\nimport sys\nsys.path.insert(0,%r)\nfrom lab2src import apply as _ap\nfrom mkrc_lib import swap as _sw\nACC=%r\nK=%r\ndef T(s): return _sw(_ap(s,ACC),K)\n'%(T,A,k)); print(n)
