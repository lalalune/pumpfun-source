#!/usr/bin/env python3
"""pair.py <m.ll> <out.jsonl> [-j N] [--pre edits.py] [--heads spec] [--ws w1;w2] [--only-heads]
Two-weight branch-frequency screen (experiment only). On post-opt IR <m.ll> (+ --pre edits, e.g. the sg skip-polarity
gate), add a !prof weight to one head branch and one other conditional br of execute, llc, and score:
ratio/bytes/slots (rx metric), wf2 F/Fw, moved (reorder.py chains out of main's order; 0 = main's layout) and, when
F >= FMIN, the sweep-gate flag's callee-saved register over the wallet (debug-greedy log; flag = the vreg tested at bb35).
Heads: start,bb1,bb6,bb9,bb12,bb2.i (the first conditional br of each block)."""
import sys,os,re,json,subprocess,tempfile,difflib,runpy
from multiprocessing import Pool
T=os.path.dirname(os.path.abspath(__file__))
g={}; exec(open(T+'/rx.py').read().split("OUT=os.environ")[0],g)
w={'__file__':T+'/wf2.py'}; exec(open(T+'/wf2.py').read().split("O=rd(")[0],w)
OR=w['rd'](open(T+'/../or.dis'))
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin'); DBG=os.path.expanduser('~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc')
LLC=['-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections']
ORIG=g['orig_window']()
REF=os.environ.get('REF_S',T+'/../rx/base/m.s')
FMIN=float(os.environ.get('FMIN','0.70'))
a=sys.argv[1:]; M=a.pop(0); OUTF=a.pop(0); J=4; PRE=None; HEADS='start,bb1,bb6,bb9,bb12,bb2.i'; HW='16,1;4,1;2,1'; WS='16,1;1,16;4,1;1,4'; ONLY=False; BRS=None
while a:
    x=a.pop(0)
    if x=='-j': J=int(a.pop(0))
    elif x=='--pre': PRE=a.pop(0)
    elif x=='--heads': HEADS=a.pop(0)
    elif x=='--hw': HW=a.pop(0)
    elif x=='--ws': WS=a.pop(0)
    elif x=='--brs': BRS=[int(v) for v in a.pop(0).split(',')]
    elif x=='--only-heads': ONLY=True
    elif x=='--single': ONLY='single'
T0=open(M).read()
if PRE:
    for e in runpy.run_path(PRE)['EDITS']:
        if callable(e): T0=e(T0); continue
        x,y=e; assert T0.count(x)==1,(T0.count(x),x[:100]); T0=T0.replace(x,y)
L=T0.split('\n')
fs=next(i for i,l in enumerate(L) if l.startswith('define') and 'admin_cto7execute17' in l)
fe=next(i for i in range(fs,len(L)) if L[i]=='}')
brs=[i for i in range(fs,fe) if re.match(r'^  br i1 %\S+, label %\S+, label %\S+$',L[i])]
def blk(i):
    for k in range(i,fs,-1):
        m=re.match(r'^("?[^ :"]+"?):',L[k])
        if m: return m.group(1)
    return 'start'
bname={i:blk(i) for i in brs}
hd={}
for h in HEADS.split(','):
    c=[i for i in brs if bname[i]==h]; assert c,h; hd[h]=c[0]
def score(t,tag,deep):
    with tempfile.TemporaryDirectory() as d:
        open(d+'/m.ll','w').write(t)
        r=subprocess.run([SDK+'/llc',*LLC,d+'/m.ll','-filetype=asm','-o',d+'/m.s'],capture_output=True,text=True)
        if r.returncode: return {**tag,'err':r.stderr[-200:]}
        r=subprocess.run([SDK+'/clang','-cc1as','-triple','sbf','-target-feature','+store-imm','-target-feature','+jmp-ext','-filetype','obj',d+'/m.s','-o',d+'/m.o'],capture_output=True,text=True)
        if r.returncode: return {**tag,'err':'as'}
        c=g['elf_fn'](d+'/m.o',g['KEEP']); rr,sd=g['metric'](c,ORIG)
        dis=subprocess.run(['bash',T+'/dis.sh',d+'/m.o'],capture_output=True,text=True).stdout.split('\n')
        C=w['rd'](dis); sm=difflib.SequenceMatcher(None,[q[1] for q in OR],[q[1] for q in C],autojunk=False)
        Mt=0;Fw=0
        for p,q,n in sm.get_matching_blocks():
            Mt+=n; Fw+=sum(1 for k in range(p,p+n) if 0x5c40<=OR[k][0]<0x6b08)
        mv=subprocess.run(['python3',T+'/reorder.py',d+'/m.s',REF,d+'/r.s'],capture_output=True,text=True).stdout.split()
        res={**tag,'ratio':round(rr,5),'bytes':len(c),'slots':sd,'F':round(sm.ratio(),5),'M':Mt,'Fw':Fw,'moved':int(mv[3]) if len(mv)>3 else None}
        if deep or res['F']>=FMIN:
            r2=subprocess.run(['python3',T+'/asmscore.py',d+'/r.s'],capture_output=True,text=True).stdout.strip()
            try: res['reord_ratio']=json.loads(r2)['ratio']
            except Exception: pass
            subprocess.run([DBG,*LLC,d+'/m.ll','-filetype=obj','-o','/dev/null','-debug-only=regalloc'],stderr=open(d+'/ra.log','w'))
            res.update(flag(d+'/ra.log'))
        return res
def flag(p):
    lg=open(p).read(); g0=lg.index('********** GREEDY'); pre=lg[:g0]
    ms=re.search(r'(\d+)B\tbb\.\d+\.bb33:',pre); me=re.search(r'(\d+)B\tbb\.\d+\.bb8[24]:',pre)
    m35=re.search(r'\d+B\tbb\.\d+\.bb35:\n(.*?)\n\d+B\tbb\.',pre,re.S)
    if not (ms and me and m35): return {'flag':'?'}
    fv=re.findall(r'J\w+_ri (%\d+):gpr, 0,',m35.group(1))
    if not fv: return {'flag':'?nojcc'}
    o=subprocess.run(['python3',T+'/csrmap.py',p,ms.group(1),me.group(1)],capture_output=True,text=True).stdout
    reg=None; cur=None; occ={}
    for l in o.split('\n'):
        if re.match(r'^r\d$',l): cur=l; continue
        q=l.split()
        if len(q)>4 and q[3]=='root':
            occ.setdefault(cur,[]).append((int(q[0]),q[4]))
            if q[4]==fv[0]: reg=(reg or '')+cur
    return {'flag':reg or 'spill','fv':fv[0],'r9':occ.get('r9',[])[:2]}
def run(job):
    kind=job[0]; LL=L[:]; md=[]
    for n,(i,wt) in enumerate(job[1]):
        LL[i]=LL[i]+', !prof !9999%d'%n; x,y=wt.split(','); md.append('!9999%d = !{!"branch_weights", i32 %s, i32 %s}'%(n,x,y))
    tag={'k':kind,'e':[[bname[i],i,wt] for i,wt in job[1]]}
    return score('\n'.join(LL)+'\n'+'\n'.join(md)+'\n',tag,kind not in('pair','single'))
if __name__=='__main__':
    jobs=[('none',[])]+[('head',[(hd[h],wt)]) for h in hd for wt in HW.split(';')]
    if ONLY=='single': jobs=[('none',[])]+[('single',[(i,wt)]) for i in (BRS or brs) for wt in WS.split(';')]
    elif not ONLY:
        for h in hd:
            for hw in HW.split(';'):
                for i in (BRS or brs):
                    if i==hd[h]: continue
                    for wt in WS.split(';'): jobs.append(('pair',[(hd[h],hw),(i,wt)]))
    print(json.dumps({'branches':len(brs),'jobs':len(jobs),'heads':hd}),flush=True)
    with Pool(J) as P, open(OUTF,'w') as f:
        for r in P.imap_unordered(run,jobs,chunksize=4): f.write(json.dumps(r)+'\n'); f.flush()
