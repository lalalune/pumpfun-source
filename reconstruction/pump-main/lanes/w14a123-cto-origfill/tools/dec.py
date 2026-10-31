#!/usr/bin/env python3
"""dec.py <orig|fn.bin> <lo-hi>...: per instruction in ranges, symbolic value read/stored (prov2 state, --opt meet)"""
import sys,os; sys.argv.append('--opt')
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import prov2, dis as D
p=sys.argv[1]; b=D.orig() if p=='orig' else open(p,'rb').read()
_,IN,ins=prov2.analyze(b); dd=dict(D.d(b))
for rg in sys.argv[2:]:
    if rg=='--opt': continue
    lo,hi=[int(x,16) for x in rg.split('-')]
    print(f'--- {lo:x}-{hi:x}')
    for (o,op,dst,src,off,imm,n) in ins:
        if not lo<=o<=hi: continue
        st=IN.get(o,{}); cls=op&7; note=''
        if cls==1:
            bs=st.get(f'r{src}')
            note= f'<= {st.get("S%d"%off)}' if bs=='FP' else f'<= {bs}.{off:x}'
        elif cls==3:
            bs=st.get(f'r{dst}'); note=f'store {st.get("r%d"%src)}' + (f' -> slot' if bs=='FP' else f' -> {bs}.{off:x}')
        elif (op&7)==5 and op not in (0x85,0x95): note=f'test r{dst}={st.get("r%d"%dst)}'
        print(f'{o:05x} {dd.get(o,""):34s} {note}')
