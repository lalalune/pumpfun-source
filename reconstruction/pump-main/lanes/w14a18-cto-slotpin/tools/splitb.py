#!/usr/bin/env python3
"""splitb.py <cand_fn> : per-access frame remap bound (each masked-aligned access takes the original's offset; text level)"""
import sys,re,difflib,subprocess,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import slotpin as S
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a,ta=S._rd(sys.argv[1]); b,tb=S._rd(O+'/orig_fn.txt'); out=list(a)
for t,i1,i2,j1,j2 in difflib.SequenceMatcher(None,ta,tb,autojunk=False).get_opcodes():
    if t!='equal': continue
    for k in range(i2-i1): out[i1+k]=b[j1+k]
L=[l.split(None,1)[0] for l in open(sys.argv[1]) if len(l.split(None,1))==2]
open('/tmp/_split.txt' if len(sys.argv)<3 else sys.argv[2],'w').write(''.join(f'{x}  {y}\n' for x,y in zip(L,out)))
print(subprocess.run(['python3',O+'/tools/oratio.py',O+'/orig_fn.txt',sys.argv[2]],capture_output=True,text=True).stdout.strip())
