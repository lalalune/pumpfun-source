#!/usr/bin/env python3
import difflib,sys,re
def rd(f): 
    r=[l.split() for l in open(f)]; return r,[re.sub(r'(\.i)?\d+$','',x[3]) if len(x)>3 else '' for x in r]
a,an=rd(sys.argv[1]); b,bn=rd(sys.argv[2])
sm=difflib.SequenceMatcher(None,an,bn,autojunk=False)
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op=='equal': print('EQ  A %s..%s (%d blk)  B %s'%(a[i1][0],a[i2-1][0],i2-i1,b[j1][0]))
    else: print(op,'A',[ (a[i][0],an[i][:24]) for i in range(i1,min(i2,i1+4))],'%d'%(i2-i1),'| B',[(b[j][0],bn[j][:24]) for j in range(j1,min(j2,j1+4))],'%d'%(j2-j1))
