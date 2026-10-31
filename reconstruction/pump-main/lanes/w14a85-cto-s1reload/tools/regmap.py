# regmap.py fn.bin lo hi [chunk]: L2-aligned insns in orig [lo,hi): register pair histogram (orig->cand) for dst/src fields, and per-0x100 mismatch
import sys,difflib,collections,struct
exec(open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a85-cto-s1reload/reconstruction/pump-main/lanes/w14a85-cto-s1reload/tools/fmr.py').read().split('def toks')[0].replace('sys.argv','[0]'))
def toks(raw,l): return [C.mask(t,l) for _,t in C.insns(raw)]
f,lo,hi=sys.argv[1],int(sys.argv[2],0),int(sys.argv[3],0)
c=open(f,'rb').read(); oi=C.insns(O); ci=C.insns(c)
sm=difflib.SequenceMatcher(None,toks(O,2),toks(c,2),autojunk=False)
P=collections.Counter(); per=collections.Counter(); rows=[]
for a,b,n in sm.get_matching_blocks():
    for k in range(n):
        oo,ot=oi[a+k]; co,ct=ci[b+k]
        if not(lo<=oo<hi): continue
        for sh in (0,4):
            x=(ot[1]>>sh)&15; y=(ct[1]>>sh)&15
            if x!=y: P[(x,y)]+=1; per[oo//0x100*0x100]+=1
        if ot[1]!=ct[1]: rows.append((oo,co))
print('reg pair mismatches (orig->cand):',', '.join('r%d->r%d:%d'%(x,y,n) for (x,y),n in P.most_common()))
print('per 0x100:',' '.join('%x:%d'%(k,v) for k,v in sorted(per.items())))
