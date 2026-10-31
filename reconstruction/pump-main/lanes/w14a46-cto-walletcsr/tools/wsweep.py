#!/usr/bin/env python3
"""wsweep.py <m.ll> <out.jsonl> [-j N] [weights]: add one !prof branch weight to each conditional br of execute
(post-opt IR) and score: plain ratio/bytes (rx metric), wf2 F/Fw, and (if F >= FMIN) whether the sweep gate flag
(root %60-like: MOV_ri phi with a single JNE 0 use at bb35) holds r9 over the wallet."""
import sys,os,re,json,subprocess,tempfile,difflib
from multiprocessing import Pool
T=os.path.dirname(os.path.abspath(__file__))
g={}; exec(open(T+'/rx.py').read().split("OUT=os.environ")[0],g)
w={'__file__':T+'/wf2.py'}; exec(open(T+'/wf2.py').read().split("O=rd(")[0],w)
OR=w['rd'](open(T+'/../or.dis'))
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin'); DBG=os.path.expanduser('~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc')
ORIG=g['orig_window']()
a=sys.argv[1:]; M=a.pop(0); OUTF=a.pop(0); J=4; WS=['20,12','12,20','16,1','1,16']; FMIN=float(os.environ.get('FMIN','0.745'))
while a:
    x=a.pop(0)
    if x=='-j': J=int(a.pop(0))
    else: WS=x.split(';')
T0=open(M).read(); L=T0.split('\n')
brs=[i for i,l in enumerate(L) if re.match(r'^  br i1 %\S+, label %\S+, label %\S+$',l)]
def run(job):
    i,wt=job; x,y=wt.split(',')
    LL=L[:]; LL[i]=LL[i]+', !prof !99995'
    t='\n'.join(LL)+'\n!99995 = !{!"branch_weights", i32 %s, i32 %s}\n'%(x,y)
    with tempfile.TemporaryDirectory() as d:
        open(d+'/m.ll','w').write(t)
        r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
        if r.returncode: return {'br':i,'w':wt,'err':1}
        c=g['elf_fn'](d+'/m.o',g['KEEP']); rr,sd=g['metric'](c,ORIG)
        dis=subprocess.run(['bash',T+'/dis.sh',d+'/m.o'],capture_output=True,text=True).stdout.split('\n')
        C=w['rd'](dis); sm=difflib.SequenceMatcher(None,[q[1] for q in OR],[q[1] for q in C],autojunk=False)
        Mt=0;Fw=0
        for p,q,n in sm.get_matching_blocks():
            Mt+=n; Fw+=sum(1 for k in range(p,p+n) if 0x5c40<=OR[k][0]<0x6b08)
        res={'br':i,'line':L[i].strip()[:80],'w':wt,'ratio':round(rr,5),'bytes':len(c),'F':round(sm.ratio(),5),'M':Mt,'Fw':Fw}
        if res['F']>=FMIN:
            subprocess.run([DBG,'-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o','/dev/null','-debug-only=regalloc'],stderr=open(d+'/ra.log','w'))
            lg=open(d+'/ra.log').read()
            ms=re.search(r'(\d+)B\tbb\.\d+\.bb33:',lg); me=re.search(r'(\d+)B\tbb\.\d+\.bb84:',lg)
            if ms and me:
                o=subprocess.run(['python3',T+'/csrmap.py',d+'/ra.log',ms.group(1),me.group(1),'r9'],capture_output=True,text=True).stdout
                res['r9']=[l.split()[1]+':'+l.split()[5] for l in o.split('\n')[1:] if l.strip()][:3]
                res['flag_r9']=bool(re.search(r'root %60 ',o))
        return res
if __name__=='__main__':
    jobs=[(i,wt) for i in brs for wt in WS]
    print(json.dumps({'branches':len(brs),'jobs':len(jobs)}),flush=True)
    with Pool(J) as P, open(OUTF,'w') as f:
        for r in P.imap_unordered(run,jobs): f.write(json.dumps(r)+'\n'); f.flush()
