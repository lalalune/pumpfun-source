import sys,difflib,re
sys.path.insert(0,'./worktrees/restore/reconstruction/harness')
from score import sections
def ro(p,sec):
    b=open(p,'rb').read(); s=sections(b)[sec]; return b[s['offset']:s['offset']+s['size']]
O=ro('./worktrees/restore/reconstruction/base/original.so',sys.argv[2])
C=ro(sys.argv[1],sys.argv[2])
sm=difflib.SequenceMatcher(None,O,C,autojunk=False)
ops=sm.get_opcodes()
eq=sum(i2-i1 for t,i1,i2,j1,j2 in ops if t=='equal')
print(len(O),len(C),'equal bytes in alignment',eq)
for t,i1,i2,j1,j2 in ops:
    if t!='equal':
        print(t,hex(i1),hex(i2),hex(j1),hex(j2),repr(O[i1:min(i2,i1+70)]),'=>',repr(C[j1:min(j2,j1+70)]))
