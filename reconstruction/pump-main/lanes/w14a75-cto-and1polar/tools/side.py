#!/usr/bin/env python3
"""side.py cand.bin lo hi : orig [lo,hi) side by side with aligned candidate (difflib on jump-masked text)."""
import sys,os,re,difflib
sys.path.insert(0,os.path.dirname(__file__)); from dis import dis
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
od=dis(open(O+'/orig.bin','rb').read()); cd=dis(open(sys.argv[1],'rb').read())
lo,hi=int(sys.argv[2],16),int(sys.argv[3],16)
def n(t): return re.sub(r', [+-]0x[0-9a-f]+$','',t)
sm=difflib.SequenceMatcher(None,[n(t) for _,t in od],[n(t) for _,t in cd],autojunk=False)
for tag,a0,a1,b0,b1 in sm.get_opcodes():
    if a1<=a0 and b1>b0:
        if not(lo<= (od[a0][0] if a0<len(od) else 1<<30) <hi): continue
    L=max(a1-a0,b1-b0)
    for k in range(L):
        a=od[a0+k] if a0+k<a1 else None; b=cd[b0+k] if b0+k<b1 else None
        if a and not(lo<=a[0]<hi): continue
        if not a and not(lo<=(od[a0][0] if a0<len(od) else 0)<hi): continue
        mk='  ' if tag=='equal' and a[1]==b[1] else ('j ' if tag=='equal' else '# ')
        print('%s%6s %-36s | %6s %s'%(mk,'%x'%a[0] if a else '',a[1] if a else '','%x'%b[0] if b else '',b[1] if b else ''))
