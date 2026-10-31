#!/usr/bin/env python3
"""mp.py <name> <m.ll> [HC=1]: code-shape ranking of a slimmed post-opt module (experiment only).
llc obj + PEI MIR (spill slots) -> M (difflib, like the scorer), Mperm (best permutation of the build's own 8 B spill
offsets: a legal recolouring, so frame-independent), Mhc (vote-suggested pairwise swap climb on top, HC=1),
true LCS (bit-parallel) unmasked, of the Mperm-relabelled code, and frame-masked (-f-). Writes rx/<name>/{fn.bin,mp.json}."""
import sys,os,json,subprocess,time
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import relab as R, lcs as LC, xled, oracle
from fact import mk
OUT=os.path.dirname(T); n,ll=sys.argv[1],sys.argv[2]; d=f'{OUT}/rx/{n}'; os.makedirs(d,exist_ok=True); t0=time.time()
L=T+'/llcp.sh'
p1=subprocess.Popen([L,ll,'-filetype=obj','-o',d+'/f.o'],stderr=subprocess.PIPE)
p2=subprocess.Popen([L,ll,'-stop-after=prologepilog','-o',d+'/pei.mir'],stderr=subprocess.PIPE)
e1=p1.communicate()[1]; p2.communicate()
if p1.returncode or p2.returncode: print(json.dumps({'n':n,'err':e1.decode()[-300:]})); sys.exit(1)
b=R.g['elf_fn'](d+'/f.o',R.g['KEEP']); open(d+'/fn.bin','wb').write(b)
sp=R.spills(d+'/pei.mir'); os.remove(d+'/pei.mir'); os.remove(d+'/f.o')
m=R.M(b); mp,pm=R.bestperm(b,sp,3); best=mp; cur=dict(pm)
if os.environ.get('HC','1')=='1':
    for rnd in range(3):
        bb=R.apply(b,cur); V=R.votes(bb,set(cur.values())); inv={v:k for k,v in cur.items()}; cand=set()
        for y,dd in V.items():
            for x in dd:
                if x in inv and x!=y: cand.add(tuple(sorted((y,x))))
        imp=0
        for y,x in sorted(cand):
            a,c=inv[y],inv[x]; t=dict(cur); t[a],t[c]=cur[c],cur[a]; mm=R.M(R.apply(b,t))
            if mm>best: best=mm; cur=t; inv={v:k for k,v in cur.items()}; imp+=1
        if not imp: break
O_=oracle.orig_window(); ot,_=xled.toks(O_)
def L_(bin_,msk): f=mk(*msk); return LC.lcs(f(ot),f(xled.toks(bin_)[0]))
bp=R.apply(b,cur)
res={'n':n,'bytes':len(b),'M':m,'Mperm':mp,'Mhc':best,'nspill':len(sp),'lcs':L_(b,(0,0,0)),'lcs_hc':L_(bp,(0,0,0)),'lcs_f':L_(b,(0,1,0)),
     'ratio':R.ratio(b),'ratio_hc':R.ratio(bp),'secs':round(time.time()-t0,1)}
json.dump(res,open(d+'/mp.json','w')); print(json.dumps(res),flush=True)
