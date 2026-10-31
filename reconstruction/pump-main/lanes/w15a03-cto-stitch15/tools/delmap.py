# delmap.py fn.bin out.json : M after deleting each single 8-byte non-jump instruction (jumps re-fixed). Experiment only.
import sys,os,struct,bisect,difflib,json,multiprocessing as mp
MYA=sys.argv[:]; T=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,T); from oracle import mask,orig_window
raw=open(MYA[1],'rb').read(); OT=mask(orig_window())
def parse(raw):
    ins=[];i=0
    while i<len(raw):
        n=16 if raw[i]==0x18 else 8; ins.append(bytes(raw[i:i+n])); i+=n
    return ins
def isj(b): op=b[0]; return (op&7) in (5,6) and op not in (0x85,0x95)
INS=parse(raw); SLOT=[0]
for b in INS: SLOT.append(SLOT[-1]+len(b)//8)
def delete(k):
    out=[]
    for j,b in enumerate(INS):
        if j==k: continue
        if isj(b):
            off=struct.unpack('<h',b[2:4])[0]; t=SLOT[j]+1+off
            ns=SLOT[j]-(1 if j>k else 0)+1; nt=t-(1 if t>SLOT[k] else 0)
            bb=bytearray(b); bb[2:4]=struct.pack('<h',nt-ns); b=bytes(bb)
        out.append(b)
    return b''.join(out)
def M(c): return sum(x.size for x in difflib.SequenceMatcher(None,OT,mask(c),autojunk=False).get_matching_blocks())
def ev(k): return (k,M(delete(k)))
if __name__=='__main__':
    ks=[k for k,b in enumerate(INS) if len(b)==8 and not isj(b) and b[0] not in (0x85,0x95)]
    with mp.get_context('fork').Pool(int(os.environ.get('NP','4'))) as P: res=P.map(ev,ks)
    base=M(raw); res.sort(key=lambda z:-z[1])
    json.dump({'base':base,'res':[(SLOT[k]*8,m) for k,m in res]},open(MYA[2],'w'))
    print('base',base,'top',[('%#x'%(SLOT[k]*8),m) for k,m in res[:25]])
