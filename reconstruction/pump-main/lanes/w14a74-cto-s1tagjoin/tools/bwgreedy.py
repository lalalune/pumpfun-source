import re,sys,subprocess,json,os
exec(open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a74-cto-s1tagjoin/reconstruction/pump-main/lanes/w14a74-cto-s1tagjoin/tools/rx.py').read().split("OUT=os.environ.get")[0])
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
base,tag=sys.argv[1],sys.argv[2]
t=open(base).read(); s=t.index('define hidden { i64, ptr } @_ZN14pump_recovered9admin_cto7execute'); e=t.index('\n}\n',s)
ms=list(re.finditer(r'\n  br i1 (%[\w.]+), label %([\w.$"]+), label %([\w.$"]+)\n',t[s:e]))
O=orig_window(); D=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a74-cto-s1tagjoin/bw/g_'+tag); os.makedirs(D,exist_ok=True)
def score(sel):
    nt=t; md=''
    for k,(i,(a,b)) in enumerate(sorted(sel.items(),reverse=True)):
        m=ms[i]; a0=s+m.start(); a1=s+m.end()-1
        nt=nt[:a0]+m.group(0)[:-1]+', !prof !%d'%(99990+k)+nt[a1:]; md+='!%d = !{!"branch_weights", i32 %d, i32 %d}\n'%(99990+k,a,b)
    open(D+'/m.ll','w').write(nt+'\n'+md)
    r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',D+'/m.ll','-filetype=obj','-o',D+'/m.o'],capture_output=True)
    c=elf_fn(D+'/m.o',KEEP); rr,sd=metric(c,O); return rr,len(c)
R=[json.loads(l) for l in open(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a74-cto-s1tagjoin/bw/%s/res.jsonl'%tag))]
R.sort(key=lambda r:-r['ratio']); cand=[(r['i'],tuple(map(int,r['w'].split(':')))) for r in R[:40]]
sel={}; best=score(sel)[0]; print('base',best)
for it in range(3):
    imp=False
    for i,w in cand:
        if sel.get(i)==w: continue
        tr=dict(sel); tr[i]=w; r,b=score(tr)
        if r>best+1e-6: best=r; sel=tr; imp=True; print('add',i,w,round(r,5),b,flush=True)
    if not imp: break
print('final',best,sel)
