# insmatch2.py fn.bin out.json : insert one ORIGINAL token (from the facing LCS gap, up to 12 per gap) at each candidate
# position inside each gap of candidate RANGE=[lo,hi); jumps re-fixed. M ceiling for one faithful extra instruction.
# (w15a01 insmatch.py, bdis/oracle based). Experiment only.
import sys,os,struct,difflib,json,multiprocessing as mp
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
from oracle import mask,orig_window
from bdis import dis
raw=open(sys.argv[1],'rb').read(); ORAW=orig_window(); OT=mask(ORAW)
def parse(raw):
    ins=[];i=0
    while i<len(raw):
        n=16 if raw[i]==0x18 else 8; ins.append(bytes(raw[i:i+n])); i+=n
    return ins
def isj(b): op=b[0]; return (op&7) in (5,6) and op not in (0x85,0x95)
INS=parse(raw); OINS=parse(ORAW); SLOT=[0]
for b in INS: SLOT.append(SLOT[-1]+len(b)//8)
def insert(k,tok):
    out=[]
    for j,b in enumerate(INS):
        if j==k: out.append(tok)
        if isj(b):
            off=struct.unpack('<h',b[2:4])[0]; t=SLOT[j]+1+off
            ns=SLOT[j]+(1 if j>=k else 0)+1; nt=t+(1 if t>=SLOT[k] else 0)
            bb=bytearray(b); bb[2:4]=struct.pack('<h',nt-ns); b=bytes(bb)
        out.append(b)
    return b''.join(out)
def M(c): return sum(x.size for x in difflib.SequenceMatcher(None,OT,mask(c),autojunk=False).get_matching_blocks())
CT=mask(raw)
sm=difflib.SequenceMatcher(None,OT,CT,autojunk=False)
lo,hi=[int(x,16) for x in os.environ.get('RANGE','6d8,18d0').split(',')]
jobs=[]
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op=='equal' or i2<=i1: continue
    if not(lo<=SLOT[min(j1,len(INS)-1)]*8<hi): continue
    for k in range(j1,min(j2+1,len(INS))):
        for i in range(i1,min(i2,i1+12)):
            if isj(OINS[i]) or OINS[i][0] in (0x85,0x95) or len(OINS[i])!=8: continue
            jobs.append((k,i))
def ev(job):
    k,i=job; return (SLOT[k]*8,i,M(insert(k,OINS[i])))
if __name__=='__main__':
    print('jobs',len(jobs),flush=True)
    if os.environ.get('COUNT'): sys.exit(0)
    with mp.get_context('fork').Pool(int(os.environ.get('NP','4'))) as P: res=P.map(ev,jobs,chunksize=8)
    base=M(raw); res.sort(key=lambda z:-z[2])
    oo=[];i=0
    while i<len(ORAW): oo.append(i); i+=16 if ORAW[i]==0x18 else 8
    do=dict(dis(ORAW))
    json.dump({'base':base,'res':[(a,oo[i],do[oo[i]],m) for a,i,m in res]},open(sys.argv[2],'w'))
    print('base',base)
    for a,i,m in res[:40]: print('%#x'%a, m, hex(oo[i]), do[oo[i]])
