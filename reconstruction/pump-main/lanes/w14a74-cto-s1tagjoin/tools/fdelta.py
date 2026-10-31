# fdelta.py fn.bin lo hi: for L2-aligned insns in orig [lo,hi) with r10 offsets, histogram of (orig_off, cand_off) pairs
import sys,difflib,collections,struct
exec(open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a74-cto-s1tagjoin/reconstruction/pump-main/lanes/w14a74-cto-s1tagjoin/tools/fmr.py').read().split('def toks')[0].replace('sys.argv','[0]'))
def toks(raw,l): return [C.mask(t,l) for _,t in C.insns(raw)]
f,lo,hi=sys.argv[1],int(sys.argv[2],0),int(sys.argv[3],0)
c=open(f,'rb').read(); oi=C.insns(O); ci=C.insns(c)
sm=difflib.SequenceMatcher(None,toks(O,2),toks(c,2),autojunk=False)
pairs=collections.Counter(); rows=[]
for a,b,n in sm.get_matching_blocks():
    for k in range(n):
        oo,ot=oi[a+k]; co,ct=ci[b+k]
        if not(lo<=oo<hi): continue
        d1=ot[1]&15; s1=ot[1]>>4
        if (ot[0]&7) in (1,2,3) and (d1==10 or s1==10):
            x=struct.unpack_from('<h',ot,2)[0]; y=struct.unpack_from('<h',ct,2)[0]
            pairs[(x,y)]+=1; rows.append((oo,co,x,y))
bad=[(x,y,n) for (x,y),n in pairs.items() if x!=y]
print('frame ops aligned',sum(pairs.values()),'equal',sum(n for (x,y),n in pairs.items() if x==y))
for x,y,n in sorted(bad): print('orig %6s cand %6s  x%d  delta %d'%(hex(x),hex(y),n,y-x))
