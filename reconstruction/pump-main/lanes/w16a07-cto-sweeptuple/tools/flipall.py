#!/usr/bin/env python3
"""flipall.py <fn.bin> <out.json>: binary polarity oracle (experiment only; assumes registers/frame unchanged, which held
for A6 and sh_iflet). -8 B: every `jCC a,b,+1; ja +X` becomes `jNCC a,b,+X`. +8 B: every conditional `jCC a,b,+X`
(X != 1, not followed by...) becomes `jNCC a,b,+1; ja +X'`. Reports M per flip."""
import sys,os,struct,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import relab as R
from concurrent.futures import ProcessPoolExecutor
INV={0x1:0x5,0x5:0x1,0x2:0xb,0xb:0x2,0x3:0xa,0xa:0x3,0x6:0xd,0xd:0x6,0x7:0xc,0xc:0x7}  # jeq<->jne, jgt<->jle, jge<->jlt, jsgt<->jsle, jsge<->jslt
def parse(raw):
    ins=[];i=0
    while i<len(raw):
        n=16 if raw[i]==0x18 else 8; ins.append(bytearray(raw[i:i+n])); i+=n
    return ins
def isj(b): op=b[0]; return (op&7) in (5,6) and op not in (0x85,0x95)
def isc(b): return isj(b) and (b[0]>>4) in INV
def off(b): return struct.unpack_from('<h',b,2)[0]
def rebuild(I,slot,ops):
    """ops: dict idx->('del') or ('ins_after', bytes) ; returns new raw with jumps re-fixed. targets kept by old slot."""
    newslot={}; s=0; seq=[]
    for idx,b in enumerate(I):
        if ops.get(idx)=='del': newslot[slot[idx]]=s; continue
        newslot[slot[idx]]=s; seq.append((idx,b,s)); s+=len(b)//8
        if isinstance(ops.get(idx),tuple): seq.append((None,ops[idx][1],s)); s+=1
    newslot[slot[len(I)]]=s
    def ns(t):  # map old target slot to new slot (deleted slot maps to next)
        while t not in newslot: t+=1
        return newslot[t]
    out=[]
    for idx,b,sn in seq:
        b=bytearray(b)
        if idx is not None and isj(b):
            t=slot[idx]+1+off(b)
            if idx in TGT: t=TGT[idx]
            struct.pack_into('<h',b,2,ns(t)-(sn+1))
        elif idx is None:
            t=b[8:] if False else None
            j=JA[0]; struct.pack_into('<h',b,2,ns(j)-(sn+1))
        out.append(bytes(b))
    return b''.join(out)
TGT={}; JA=[0]
def flip_minus(raw,k):
    I=parse(raw); slot=[0]
    for b in I: slot.append(slot[-1]+len(b)//8)
    c=I[k]; ja=I[k+1]; X=slot[k+1]+1+off(ja)
    c[0]=(INV[c[0]>>4]<<4)|(c[0]&0xf)
    TGT.clear(); TGT[k]=X
    return rebuild(I,slot,{k+1:'del'})
def flip_plus(raw,k):
    I=parse(raw); slot=[0]
    for b in I: slot.append(slot[-1]+len(b)//8)
    c=I[k]; X=slot[k]+1+off(c)
    c[0]=(INV[c[0]>>4]<<4)|(c[0]&0xf)
    TGT.clear(); TGT[k]=slot[k+1]   # new cond jumps to old fallthrough (next insn), which follows the inserted ja
    JA[0]=X
    ja=bytearray(8); ja[0]=0x05
    # cond target must be the instruction after the inserted ja: old slot k+1 maps to the ja's slot; fix by +1
    raw2=rebuild(I,slot,{k:('ins',bytes(ja))})
    I2=parse(raw2); s2=[0]
    for b in I2: s2.append(s2[-1]+len(b)//8)
    # find the inserted ja index: k+1 in I2; cond at k must jump +1
    b=I2[k]; struct.pack_into('<h',b,2,1)
    return b''.join(bytes(x) for x in I2)
def sites(raw):
    I=parse(raw); m=[];p=[]
    for k in range(len(I)-1):
        if isc(I[k]) and off(I[k])==1 and I[k+1][0]==0x05: m.append(k)
        elif isc(I[k]) and off(I[k])!=1 and not (k>0 and isc(I[k-1]) and off(I[k-1])==1): p.append(k)
    return m,p
RAW=None
def evm(k): return ('-',k,R.M(flip_minus(RAW,k)))
def evp(k): return ('+',k,R.M(flip_plus(RAW,k)))
if __name__=='__main__':
    RAW=open(sys.argv[1],'rb').read(); m,p=sites(RAW)
    I=parse(RAW); slot=[0]
    for b in I: slot.append(slot[-1]+len(b)//8)
    import multiprocessing as _mp
    with ProcessPoolExecutor(int(os.environ.get('NP','4')),mp_context=_mp.get_context('fork')) as ex:
        res=list(ex.map(evm,m,chunksize=4))+list(ex.map(evp,p,chunksize=4))
    out=[{'kind':a,'k':k,'off':slot[k]*8,'M':M} for a,k,M in res]
    json.dump({'base':R.M(RAW),'res':out},open(sys.argv[2],'w'))
    for d in sorted(out,key=lambda d:-d['M'])[:15]: print(d['kind'],hex(d['off']),d['M'])
