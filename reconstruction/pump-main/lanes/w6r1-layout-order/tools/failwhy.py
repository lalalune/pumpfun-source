import sys,json,re
from collections import Counter
sys.path.insert(0,__file__.rsplit('/',1)[0])
from m13 import *
M=model(sys.argv[1],sys.argv[2])
base=M.eval(M.cst)
na={a:a for a in M.cst}
cnt=Counter(); ex=[]
for st,a,calls,tl,hd in M.checks:
    if st in base: continue
    bad=[]
    for off,c,coff,od in calls:
        err=(c+coff-(a+off+8))-od
        if err: bad.append((c,err))
    for c,coff,oabs in tl:
        if c+coff!=oabs: bad.append((c,'tl'))
    kind=('data+' if hd else '')+('calls' if bad else 'nocall')
    errs=sorted(set(e for c,e in bad if e!='tl'))
    reg=sorted(set(M.region(c) for c,e in bad))
    cnt[(kind,tuple(reg))]+=1
    if not hd: ex.append((hex(st),M.region(a),[ (M.region(c),hex(M.inv.get(c,0)),e) for c,e in bad][:6]))
print(cnt)
for e in ex: print(e)
