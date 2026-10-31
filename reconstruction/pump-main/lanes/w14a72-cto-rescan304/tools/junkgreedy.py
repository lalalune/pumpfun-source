# junkgreedy.py fn.bin rounds : greedy upper bound of pure +8 B junk insertions (jumps fixed), reports cumulative M
import sys,os,struct,bisect,difflib,multiprocessing as mp
MYA=sys.argv[:]; T=os.path.dirname(os.path.abspath(__file__))
sys.argv=['x','n']; exec(open(T+'/rx.py').read().split('OUT=os.environ')[0])
raw=open(MYA[1],'rb').read(); R=int(MYA[2]); STEP=int(os.environ.get('STEP','3'))
OT=mask(orig_window())
def parse(raw):
    ins=[];i=0
    while i<len(raw):
        n=16 if raw[i]==0x18 else 8; ins.append(bytes(raw[i:i+n])); i+=n
    return ins
def isj(b): op=b[0]; return (op&7) in (5,6) and op not in (0x85,0x95)
def insert(raw,k):
    ins=parse(raw); slot=[0]
    for b in ins: slot.append(slot[-1]+len(b)//8)
    out=[]
    for j,b in enumerate(ins):
        if j==k: out.append(b'\xfe'*8)
        if isj(b):
            off=struct.unpack('<h',b[2:4])[0]; t=slot[j]+len(b)//8+off
            ti=bisect.bisect_left(slot,t)
            ns=slot[j]+(1 if j>=k else 0)+len(b)//8; nt=slot[ti]+(1 if ti>=k and not (ti==k) else 0)
            if ti==k: nt=slot[ti]   # jump to block start k lands on the junk slot (block start moves down)
            bb=bytearray(b); bb[2:4]=struct.pack('<h',nt-ns); b=bytes(bb)
        out.append(b)
    return b''.join(out)
def M(c): return sum(x.size for x in difflib.SequenceMatcher(None,OT,mask(c),autojunk=False).get_matching_blocks())
def ev(args): raw,k=args; return (k,M(insert(raw,k)))
if __name__=='__main__':
    cur=raw; print('base',M(cur),len(cur),flush=True)
    for r in range(R):
        n=len(parse(cur)); ks=list(range(1,n,STEP))
        with mp.get_context('fork').Pool(int(os.environ.get('NP','4'))) as P: res=P.map(ev,[(cur,k) for k in ks])
        res.sort(key=lambda z:-z[1]); k,m=res[0]
        offs=[0]
        for b in parse(cur): offs.append(offs[-1]+len(b))
        cur=insert(cur,k); print('round',r,'insert at %#x'%offs[k],'M',m,'bytes',len(cur),'top',[('%#x'%offs[a],b) for a,b in res[:6]],flush=True)
