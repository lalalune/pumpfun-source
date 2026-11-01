#!/usr/bin/env python3
"""regs.py <fn.bin>...: per-region (w17a01 boundaries) original tokens matched at scorer mask (m0) and full mask (m3)."""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import skel,oracle,d as D
REG={'E1':(0,0x280),'E2':(0x280,0x420),'E3':(0x420,0x708),'V':(0x708,0x1800),'J1':(0x1800,0x1990),'J2':(0x1990,0x1c88),'W1S1':(0x1c88,0x26e8),'T1':(0x26e8,0x3c50),'C1':(0x3c50,0x4aa8),'P1EV':(0x4aa8,0x5558),'tail':(0x5558,0x6b08)}
O=oracle.orig_window()
offs=[];i=0
while i<len(O): offs.append(i); i+=16 if O[i]==0x18 else 8
def run(b,mode):
    sm=difflib.SequenceMatcher(None,skel.toks(O,mode),skel.toks(b,mode),autojunk=False)
    hit=[0]*len(offs)
    for blk in sm.get_matching_blocks():
        for k in range(blk.a,blk.a+blk.size): hit[k]=1
    r={k:sum(hit[n] for n,o in enumerate(offs) if lo<=o<hi) for k,(lo,hi) in REG.items()}; r['ALL']=sum(hit); return r
print('%-12s    '%'region'+' '.join('%5s'%k for k in list(REG)+['ALL']))
print('%-12s    '%'orig'+' '.join('%5d'%sum(1 for o in offs if lo<=o<hi) for k,(lo,hi) in REG.items())+' %5d'%len(offs))
for p in sys.argv[1:]:
    b=D.load(p)
    for mode in [int(x) for x in os.environ.get("MODES","0,3").split(",")]:
        r=run(b,mode); print('%-12s m%d '%((os.path.basename(os.path.dirname(p)) or p)[:12],mode)+' '.join('%5d'%r[k] for k in list(REG)+['ALL']))
