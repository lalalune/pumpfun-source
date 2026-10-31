#!/usr/bin/env python3
"""postjoin.py <m.ll> <out.ll> [variant]: experiment-only post-opt IR edit. Moves validate's target copy out of the
pre-tree join bb76 into the post-tree join bb26 (phi of source pointers), as in the original's post-tree target copy.
variant 'keep9' keeps the 9-byte hop through _48.sroa.11 in bb76."""
import sys,re
src,dst=sys.argv[1],sys.argv[2]; var=sys.argv[3] if len(sys.argv)>3 else ''
t=open(src).read()
def blk(t,needle):
    k=t.index(needle); i=t.rindex('\n\n',0,k)+2; j=t.index('\n\n',k); return i,j
i,j=blk(t,'dereferenceable(7) %target.sroa.0, ptr noundef nonnull align 1 dereferenceable(7) %target.i.sroa.0,'); b76=t[i:j]
def drop(b,pat):
    ls=b.split('\n'); k=[x for x in ls if re.search(pat,x)]; assert len(k)==1,(pat,k); return '\n'.join(x for x in ls if x is not k[0])
b=b76
b=drop(b,r'memcpy.*%target\.sroa\.0, ptr .*%target\.i\.sroa\.0,')
b=drop(b,r'lifetime\.end.*%target\.i\.sroa\.0\)')
if var!='keep9':
    b=drop(b,r'memcpy.*%_48\.sroa\.11, ptr .*%target\.i\.sroa\.9,')
    b=drop(b,r'lifetime\.end.*%target\.i\.sroa\.9\)')
    b=drop(b,r'memcpy.*%target\.sroa\.8, ptr .*%_48\.sroa\.11,')
t=t[:i]+b+t[j:]
i,j=blk(t,'dereferenceable(7) %target13, ptr noundef nonnull align 1 dereferenceable(7) %target.sroa.0,'); b26=t[i:j]
own=[q for q in re.findall(r'^(bb\d+):',t,re.M) if 0]
ls=b26.split('\n'); hdr=ls[0]; preds=re.findall(r'%([\w.]+)',hdr.split('preds =')[1])
def body(name):
    a=t.index('\n'+name+':')+1; return t[a:t.index('\n\n',a)]
OWN=[q for q in preds if 'dereferenceable(7) %target.sroa.0, ptr' in body(q)]; assert len(OWN)==1,OWN; OWN=OWN[0]
n=max(k for k,x in enumerate(ls) if ' = phi ' in x)
def ph(name,own,other): return f'  %{name} = phi ptr '+', '.join(f'[ %{own if p==OWN else other}, %{p} ]' for p in preds)
new=[ph('pj7','target.sroa.0','target.i.sroa.0')]
if var!='keep9': new.append(ph('pj9','target.sroa.8','target.i.sroa.9'))
ls=ls[:n+1]+new+ls[n+1:]; print('join',ls[0][:12],'preds',preds,'own',OWN)
b=('\n'.join(ls))
b=b.replace('dereferenceable(7) %target.sroa.0, i64 7','dereferenceable(7) %pj7, i64 7',1)
if var!='keep9': b=b.replace('dereferenceable(9) %target.sroa.8, i64 9','dereferenceable(9) %pj9, i64 9',1)
t=t[:i]+b+t[j:]
open(dst,'w').write(t)
