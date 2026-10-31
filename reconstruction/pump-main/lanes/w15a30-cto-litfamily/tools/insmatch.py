# insmatch.py fn.bin out.json : like insmap.py, but inserts an ORIGINAL token (from the facing LCS gap) instead of junk,
# at each candidate position inside each gap of [RANGE). Upper bound for "one faithful extra instruction". Experiment only.
import sys,os,struct,difflib,json,multiprocessing as mp
MYA=sys.argv[:]; T=os.path.dirname(os.path.abspath(__file__))
sys.argv=['x','n']; exec(open(T+'/rx.py').read().split('OUT=os.environ')[0])
raw=open(MYA[1],'rb').read(); ORAW=orig_window(); OT=mask(ORAW)
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
# map token index -> instruction index (token per instruction)
sm=difflib.SequenceMatcher(None,OT,CT,autojunk=False)
lo,hi=[int(x,16) for x in os.environ.get('RANGE','6d8,18d0').split(',')]
jobs=[]
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op=='equal' or i2<=i1: continue
    if not(lo<=SLOT[j1]*8<hi): continue
    for k in range(j1,j2+1):
        for i in range(i1,min(i2,i1+12)):
            if isj(OINS[i]) or OINS[i][0]==0x85: continue
            jobs.append((k,i))
def ev(job):
    k,i=job; return (SLOT[k]*8,i,M(insert(k,OINS[i])))
if __name__=='__main__':
    print('jobs',len(jobs),flush=True)
    with mp.get_context('fork').Pool(int(os.environ.get('NP','4'))) as P: res=P.map(ev,jobs)
    base=M(raw); res.sort(key=lambda z:-z[2])
    sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a109-cto-stitch13/tools'); import dis as D
    do=dict((n,t) for n,(a,t) in enumerate(D.d(ORAW)))
    json.dump({'base':base,'res':res},open(MYA[2],'w'))
    print('base',base)
    for a,i,m in res[:40]: print('%#x'%a, m, do.get(i))
