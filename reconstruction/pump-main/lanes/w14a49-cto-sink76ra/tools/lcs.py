import sys
from difflib import SequenceMatcher
from dis import calls
o=calls(sys.argv[1]); c=calls(sys.argv[2])
print(len(o),len(c))
sm=SequenceMatcher(None,[x[1] for x in o],[x[1] for x in c],autojunk=False)
n=0
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal':
        n+=i2-i1
        prev=None
        for i,j in zip(range(i1,i2),range(j1,j2)):
            dd=c[j][0]-o[i][0]
            if dd!=prev: print('  EQ from orig+%x ours+%x disp %+#x'%(o[i][0],c[j][0],dd)); prev=dd
    else:
        print(tag,[('+%x'%o[i][0],hex(o[i][1])) for i in range(i1,i2)],[('+%x'%c[j][0],hex(c[j][1])) for j in range(j1,j2)])
print('lcs',n)
