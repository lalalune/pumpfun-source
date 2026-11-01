#!/usr/bin/env python3
"""marker.py <fn.bin>...: registers of the first TCF program clone (AccountInfo at [acc+0x58]) in the sweep.
orig: lamports r7, key r9, data r0, E r5, O r6. Prints JSON per file."""
import sys,os,json,struct
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import bdis
F={0x0:'key',0x8:'lam',0x10:'data',0x18:'own',0x20:'re',0x28:'sig',0x29:'wr',0x2a:'E'}
def decode(b):
    i=0; out=[]
    while i<len(b):
        op,r,off,imm=struct.unpack_from('<BBhi',b,i); n=16 if op==0x18 else 8
        out.append((i,op,r&15,r>>4,off,imm)); i+=n
    return out
def marker(b,lo=0x1c00,hi=0x3400):
    I=decode(b)
    for k,(o,op,dst,src,off,imm) in enumerate(I):
        if not(lo<=o<hi): continue
        if op==0x79 and off==0x58:  # ldxdw dst,[src+0x58]
            A=dst; res={'at':hex(o)}
            ok=False
            for (o2,op2,d2,s2,off2,imm2) in I[k+1:k+40]:
                if op2 in (0x79,0x71) and s2==A and off2 in F and F[off2] not in res:
                    res[F[off2]]=f'r{d2}'
                    if off2==0x8: ok=True
                if d2==A and ((op2&7) in (1,4,7) or op2==0x18): break
            if ok: return res
    return None
if __name__=='__main__':
    for p in sys.argv[1:]:
        print(json.dumps({'p':p,'m':marker(open(p,'rb').read())}))
