# bwsweep.py base_m.ll tag weights...: for every conditional br in execute, set !prof weights and score via llc (single-edit sweep)
import re,sys,subprocess,json,os
exec(open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a74-cto-s1tagjoin/reconstruction/pump-main/lanes/w14a74-cto-s1tagjoin/tools/rx.py').read().split("OUT=os.environ.get")[0])
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
base,tag=sys.argv[1],sys.argv[2]; W=[tuple(map(int,w.split(':'))) for w in sys.argv[3:]]
t=open(base).read(); s=t.index('define hidden { i64, ptr } @_ZN14pump_recovered9admin_cto7execute'); e=t.index('\n}\n',s)
ms=list(re.finditer(r'\n  br i1 (%[\w.]+), label %([\w.$"]+), label %([\w.$"]+)\n',t[s:e]))
O=orig_window(); D='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a74-cto-s1tagjoin/bw/'+tag
os.makedirs(D,exist_ok=True)
out=open(D+'/res.jsonl','a')
for i,m in enumerate(ms):
    for a,b in W:
        a0=s+m.start(); a1=s+m.end()-1
        nt=t[:a0]+m.group(0)[:-1]+', !prof !99990'+t[a1:]+'\n!99990 = !{!"branch_weights", i32 %d, i32 %d}\n'%(a,b)
        open(D+'/m.ll','w').write(nt)
        r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',D+'/m.ll','-filetype=obj','-o',D+'/m.o'],capture_output=True)
        if r.returncode: continue
        c=elf_fn(D+'/m.o',KEEP); rr,sd=metric(c,O)
        out.write(json.dumps({'i':i,'cond':m.group(1),'yes':m.group(2),'no':m.group(3),'w':'%d:%d'%(a,b),'ratio':round(rr,5),'bytes':len(c)})+'\n'); out.flush()
