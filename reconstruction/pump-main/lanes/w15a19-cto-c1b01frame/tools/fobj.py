#!/usr/bin/env python3
"""fobj.py <a/pei.mir> <b/pei.mir>: side-by-side non-spill frame objects (offset,size,name) of two llc -stop-after=prologepilog dumps,
plus spill-slot count and range. Shows which alloca an edit adds and how far it pushes the objects below it."""
import sys,re
def objs(p):
    t=open(p).read(); st=t[t.index('\nstack:'):]; st=st[:st.index('\ncallSites:')] if '\ncallSites:' in st else st[:40000]
    R=[]
    for blk in re.split(r'\n  - \{ ',st)[1:]:
        d=dict(re.findall(r"(\w[\w-]*): ('[^']*'|[^,}]+)",blk))
        R.append((int(d.get('offset','0')),int(d.get('size','0')),d.get('type',''),d.get('name','').strip("'")))
    return R
a,b=objs(sys.argv[1]),objs(sys.argv[2])
for n,x in (('a',a),('b',b)):
    s=[o for o,_,t,_ in x if t=='spill-slot']; print(n,'spills',len(s),hex(min(s)),hex(max(s)))
A=sorted([x for x in a if x[2]!='spill-slot'],reverse=True); B=sorted([x for x in b if x[2]!='spill-slot'],reverse=True)
for i in range(max(len(A),len(B))):
    x=A[i] if i<len(A) else None; y=B[i] if i<len(B) else None
    f=lambda z:f'{z[0]:#7x} {z[1]:4d} {z[3]:24s}' if z else ' '*37
    print(f(x),'|',f(y))
