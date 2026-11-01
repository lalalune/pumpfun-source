#!/usr/bin/env python3
"""insdel.py <fn.bin> <ins_off_hex> <out.json>: bound for a (+8 B at one position, -8 B elsewhere) knob pair: insert one
junk slot before the instruction at ins_off and delete each single non-jump 8 B instruction q in turn (jumps re-fixed),
scoring M. Experiment only (binary edit bound, never a source proposal)."""
import sys,os,struct,difflib,json,multiprocessing as mp
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
from oracle import mask,orig_window
raw=open(sys.argv[1],'rb').read(); AT=int(sys.argv[2],16); OT=mask(orig_window()); JUNK=bytes([0xff,0,0,0,0,0,0,0])
def parse(raw):
    ins=[];i=0
    while i<len(raw):
        n=16 if raw[i]==0x18 else 8; ins.append(bytes(raw[i:i+n])); i+=n
    return ins
def isj(b): op=b[0]; return (op&7) in (5,6) and op not in (0x85,0x95)
INS=parse(raw); SLOT=[0]
for b in INS: SLOT.append(SLOT[-1]+len(b)//8)
KI=[k for k in range(len(INS)) if SLOT[k]*8==AT][0]
def build(kd):
    # new slot of old slot s: +1 if s>=SLOT[KI] (insert before KI), -1 if s>SLOT[kd] (delete kd)
    def ns(s): return s+(1 if s>=SLOT[KI] else 0)-(1 if s>SLOT[kd] else 0)
    out=[]
    for j,b in enumerate(INS):
        if j==KI: out.append(JUNK)
        if j==kd: continue
        if isj(b):
            off=struct.unpack('<h',b[2:4])[0]; t=SLOT[j]+1+off
            src=ns(SLOT[j])+1; bb=bytearray(b); bb[2:4]=struct.pack('<h',ns(t)-src); b=bytes(bb)
        out.append(b)
    return b''.join(out)
def M(c): return sum(x.size for x in difflib.SequenceMatcher(None,OT,mask(c),autojunk=False).get_matching_blocks())
def ev(k): return (SLOT[k]*8,M(build(k)))
if __name__=='__main__':
    ks=[k for k,b in enumerate(INS) if len(b)==8 and not isj(b) and b[0] not in (0x85,0x95) and k!=KI]
    with mp.get_context('fork').Pool(int(os.environ.get('NP','3'))) as P: res=P.map(ev,ks,chunksize=16)
    res.sort(key=lambda z:-z[1]); json.dump({'ins':hex(AT),'res':res},open(sys.argv[3],'w'))
    import collections
    print('ins',hex(AT),'hist',sorted(collections.Counter(m for _,m in res).items())[-5:],'top',[(hex(a),m) for a,m in res[:15]])
