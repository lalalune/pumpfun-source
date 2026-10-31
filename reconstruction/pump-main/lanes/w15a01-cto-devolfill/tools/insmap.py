# insmap.py fn.bin out.json : M after inserting one 8-byte junk slot before each instruction (jumps re-fixed). Experiment only.
# Finds where a +8 B source change would repay a -8 B base (inverse of w14a119 delmap.py).
import sys,os,struct,difflib,json,multiprocessing as mp
MYA=sys.argv[:]; T=os.path.dirname(os.path.abspath(__file__))
sys.argv=['x','n']; exec(open(T+'/rx.py').read().split('OUT=os.environ')[0])
raw=open(MYA[1],'rb').read(); OT=mask(orig_window())
JUNK=bytes([0xff,0,0,0,0,0,0,0])
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
        if j==k: out.append(JUNK)
        if isj(b):
            off=struct.unpack('<h',b[2:4])[0]; t=SLOT[j]+1+off
            ns=SLOT[j]+(1 if j>=k else 0)+1; nt=t+(1 if t>=SLOT[k] else 0)
            bb=bytearray(b); bb[2:4]=struct.pack('<h',nt-ns); b=bytes(bb)
        out.append(b)
    return b''.join(out)
def M(c): return sum(x.size for x in difflib.SequenceMatcher(None,OT,mask(c),autojunk=False).get_matching_blocks())
def ev(k): return (k,M(insert(k)))
if __name__=='__main__':
    lo,hi=[int(x,16) for x in os.environ.get('RANGE','0,7000').split(',')]
    ks=[k for k in range(len(INS)) if lo<=SLOT[k]*8<hi]
    with mp.get_context('fork').Pool(int(os.environ.get('NP','4'))) as P: res=P.map(ev,ks)
    base=M(raw); res.sort(key=lambda z:-z[1])
    json.dump({'base':base,'res':[(SLOT[k]*8,m) for k,m in res]},open(MYA[2],'w'))
    print('base',base,'top',[('%#x'%(SLOT[k]*8),m) for k,m in res[:30]])
