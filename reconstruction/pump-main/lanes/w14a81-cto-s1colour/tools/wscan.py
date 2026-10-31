#!/usr/bin/env python3
"""wscan.py <m.ll> <out.jsonl> [-j N] [--pre i:a:b,...] [--ws a:b;c:d] [--brs i,j] [--only]  (experiment only)
Branch-weight screen on an rx post-opt module. --pre fixes weights on branch indices (index = order of the
conditional `br i1` in execute, as bwsweep.py). Each job adds one more weight on another branch. Scores the plain
rx ratio, fmr L0/L1/L2, M (matched orig insns, plain) and cls fm/rm/jm/sk over the sharing CPI (orig 0x3c38-0x46b8)."""
import sys,os,re,json,subprocess,tempfile,difflib,types
from multiprocessing import Pool
T=os.path.dirname(os.path.abspath(__file__))
g={'__name__':'x'}; s_=open(T+'/rx.py').read(); exec(s_[:s_.index("OUT=os.environ.get")],g)
C=types.ModuleType('C'); _s=open(T+'/cls.py').read(); C.__dict__['__file__']=T+'/cls.py'; exec(_s[:_s.index('def main')],C.__dict__)
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
O=g['orig_window'](); OI=C.insns(O); OT=[[C.mask(t,l) for _,t in OI] for l in range(4)]
LO,HI=0x3c38,0x46b8
a=sys.argv[1:]; M=a.pop(0); OUTF=a.pop(0); J=4; PRE=[]; WS='8:1;1:8;2000:1;1:2000'; BRS=None; ONLY=False
while a:
    x=a.pop(0)
    if x=='-j': J=int(a.pop(0))
    elif x=='--pre': PRE=[tuple(int(v) for v in p.split(':')) for p in a.pop(0).split(',') if p]
    elif x=='--ws': WS=a.pop(0)
    elif x=='--brs': BRS=[int(v) for v in a.pop(0).split(',')]
    elif x=='--only': ONLY=True
t=open(M).read(); s=t.index('define hidden { i64, ptr } @_ZN14pump_recovered9admin_cto7execute'); e=t.index('\n}\n',s)
ms=list(re.finditer(r'\n  br i1 (%[\w.]+), label %([\w.$"]+), label %([\w.$"]+)\n',t[s:e]))
def build(ws):
    reps=sorted(((s+ms[i].start(),s+ms[i].end()-1,i,a_,b_) for i,a_,b_ in ws),reverse=True); nt=t; md=[]
    for n,(a0,a1,i,a_,b_) in enumerate(reps):
        nt=nt[:a1]+', !prof !9999%d'%n+nt[a1:]; md.append('!9999%d = !{!"branch_weights", i32 %d, i32 %d}'%(n,a_,b_))
    return nt+'\n'+'\n'.join(md)+'\n'
def region(c):
    CI=C.insns(c); oc=C.calls(OI); cc=C.calls(CI)
    def cidx(off): return sum(1 for x in oc if x<off)
    def cmap(off,k):
        bo=oc[k-1] if k else -8; bc=cc[k-1] if k else -8
        n=len([1 for o,_ in OI if bo<o<off]); seg=[o for o,_ in CI if o>bc]
        return seg[n] if n<len(seg) else len(c)
    if len(cc)!=len(oc): return {}
    clo,chi=cmap(LO,cidx(LO)),cmap(HI,cidx(HI))
    Or=[t_ for o,t_ in OI if LO<=o<HI]; Cr=[t_ for o,t_ in CI if clo<=o<chi]; miss=[]
    for L in range(4):
        sm=difflib.SequenceMatcher(None,[C.mask(x,L) for x in Or],[C.mask(x,L) for x in Cr],autojunk=False)
        miss.append(len(Or)-sum(b.size for b in sm.get_matching_blocks()))
    for L in range(1,4): miss[L]=min(miss[L],miss[L-1])
    return {'miss':miss[0],'fm':miss[0]-miss[1],'rm':miss[1]-miss[2],'jm':miss[2]-miss[3],'sk':miss[3]}
def run(ws):
    with tempfile.TemporaryDirectory() as d:
        open(d+'/m.ll','w').write(build(ws))
        r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
        if r.returncode: return {'w':ws,'err':r.stderr[-200:]}
        c=g['elf_fn'](d+'/m.o',g['KEEP'])
    rr,sd=g['metric'](c,O); CI=C.insns(c); L=[]
    for l in range(3):
        sm=difflib.SequenceMatcher(None,OT[l],[C.mask(x,l) for _,x in CI],autojunk=False); L.append(round(sm.ratio(),5))
    import struct as _st
    p3=[hex(-_st.unpack('<h',x[2:4])[0]) for _,x in CI[:6] if x[0]==0x7b and (x[1]&15)==10]
    return {'w':ws,'ratio':round(rr,5),'bytes':len(c),'slots':sd,'L':L,'pro':p3,**region(c)}
if __name__=='__main__':
    W=[tuple(int(v) for v in w.split(':')) for w in WS.split(';')]
    pre=[p[0] for p in PRE]
    jobs=[list(PRE)]
    if not ONLY: jobs+=[list(PRE)+[(i,a_,b_)] for i in (BRS or range(len(ms))) if i not in pre for a_,b_ in W]
    print(json.dumps({'branches':len(ms),'jobs':len(jobs)}),flush=True)
    with Pool(J) as P, open(OUTF,'w') as f:
        for r in P.imap_unordered(run,jobs,chunksize=2): f.write(json.dumps(r)+'\n'); f.flush()
