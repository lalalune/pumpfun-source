#!/usr/bin/env python3
"""insmapn.py fn.bin out.json [N]: M after inserting N contiguous 8-byte junk slots before each instruction (jumps re-fixed).
Experiment only. Generalises w14a138/w15a01 insmap.py to an N-slot run: where would a faithful +8N B construct repay a
-8N B base. RANGE=lo,hi (hex, candidate offsets), NP workers."""
import sys,os,struct,difflib,json,multiprocessing as mp
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
from oracle import mask,orig_window
raw=open(sys.argv[1],'rb').read(); OUTF=sys.argv[2]; N=int(sys.argv[3]) if len(sys.argv)>3 else 1
OT=mask(orig_window()); JUNK=bytes([0xff,0,0,0,0,0,0,0])
def parse(raw):
    ins=[];i=0
    while i<len(raw):
        n=16 if raw[i]==0x18 else 8; ins.append(bytes(raw[i:i+n])); i+=n
    return ins
def isj(b): op=b[0]; return (op&7) in (5,6) and op not in (0x85,0x95)
INS=parse(raw); SLOT=[0]
for b in INS: SLOT.append(SLOT[-1]+len(b)//8)
def insert(k):
    out=[]
    for j,b in enumerate(INS):
        if j==k: out.extend([JUNK]*N)
        if isj(b):
            off=struct.unpack('<h',b[2:4])[0]; t=SLOT[j]+1+off
            ns=SLOT[j]+(N if j>=k else 0)+1; nt=t+(N if t>=SLOT[k] else 0)
            bb=bytearray(b); bb[2:4]=struct.pack('<h',nt-ns); b=bytes(bb)
        out.append(b)
    return b''.join(out)
def M(c): return sum(x.size for x in difflib.SequenceMatcher(None,OT,mask(c),autojunk=False).get_matching_blocks())
def ev(k): return (k,M(insert(k)))
if __name__=='__main__':
    lo,hi=[int(x,16) for x in os.environ.get('RANGE','0,7000').split(',')]
    ks=[k for k in range(len(INS)) if lo<=SLOT[k]*8<hi]
    with mp.get_context('fork').Pool(int(os.environ.get('NP','4'))) as P: res=P.map(ev,ks,chunksize=8)
    base=M(raw); res.sort(key=lambda z:-z[1])
    json.dump({'base':base,'N':N,'res':[(SLOT[k]*8,m) for k,m in res]},open(OUTF,'w'))
    import collections
    print('base',base,'N',N,'hist',sorted(collections.Counter(m for _,m in res).items())[-6:],'top',[('%#x'%(SLOT[k]*8),m) for k,m in res[:12]])
