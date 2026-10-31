import sys,os,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import lab2src as L
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
