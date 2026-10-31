#!/usr/bin/env python3
"""shift2.py STEP fn.bin..: median (cand-orig) offset of jump-masked aligned insns per STEP orig region."""
import sys,os,re,difflib,statistics
sys.path.insert(0,os.path.dirname(__file__)); from dis import dis
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def n(t): return re.sub(r', [+-]0x[0-9a-f]+$','',re.sub(r'call .*','call',re.sub(r'lddw (r\d+), .*',r'lddw \1',t)))
od=dis(open(O+'/orig.bin','rb').read()); W=int(sys.argv[1],16)
for f in sys.argv[2:]:
    cd=dis(open(f,'rb').read()); sm=difflib.SequenceMatcher(None,[n(t) for _,t in od],[n(t) for _,t in cd],autojunk=False); d={}
    for a,b,s in sm.get_matching_blocks():
        for i in range(s): d.setdefault(od[a+i][0]//W,[]).append(cd[b+i][0]-od[a+i][0])
    print(f.split('/')[-2],' '.join('%x:%+d'%(k*W,int(statistics.median(v))) for k,v in sorted(d.items()) if len(v)>6))
