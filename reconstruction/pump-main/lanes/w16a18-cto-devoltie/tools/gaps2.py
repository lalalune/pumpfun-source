# gaps2.py fn.bin lo hi : LCS (masked tokens) gaps between orig and candidate over candidate range [lo,hi) (w15a01 gaps.py, bdis-based).
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
from oracle import mask,orig_window
from bdis import dis
o=orig_window(); c=open(sys.argv[1],'rb').read(); lo,hi=int(sys.argv[2],16),int(sys.argv[3],16)
do=dis(o); dc=dis(c); mo=mask(o); mc=mask(c)
sm=difflib.SequenceMatcher(None,mo,mc,autojunk=False)
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op=='equal': continue
    jj=min(j1,len(dc)-1)
    if not(lo<=dc[jj][0]<hi): continue
    print(f'{op:7s} O: '+' | '.join(f'{do[i][0]:x} {do[i][1]}' for i in range(i1,i2)))
    print(f'        C: '+' | '.join(f'{dc[j][0]:x} {dc[j][1]}' for j in range(j1,j2)))
