# gaps.py fn.bin lo hi : LCS (masked tokens) gaps between orig and candidate, candidate range [lo,hi). Experiment only.
import sys,os,difflib
MYA=sys.argv[:]; T=os.path.dirname(os.path.abspath(__file__))
sys.argv=['x','n']; exec(open(T+'/rx.py').read().split('OUT=os.environ')[0])
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a109-cto-stitch13/tools'); import dis as D
o=orig_window(); c=open(MYA[1],'rb').read(); lo,hi=int(MYA[2],16),int(MYA[3],16)
do=D.d(o); dc=D.d(c); mo=mask(o); mc=mask(c)
sm=difflib.SequenceMatcher(None,mo,mc,autojunk=False)
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op=='equal': continue
    if j2<=j1 and not(lo<=dc[min(j1,len(dc)-1)][0]<hi): continue
    if j2>j1 and not(lo<=dc[j1][0]<hi): continue
    print(f'{op:7s} O: '+' | '.join(f'{do[i][0]:x} {do[i][1]}' for i in range(i1,i2)))
    print(f'        C: '+' | '.join(f'{dc[j][0]:x} {dc[j][1]}' for j in range(j1,j2)))
