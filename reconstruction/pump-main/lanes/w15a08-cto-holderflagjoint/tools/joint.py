import sys; sys.path.insert(0,'tools'); import relab as R, difflib
g=R.g
mb=g['elf_fn']('d/main/f.o',g['KEEP']); eb=g['elf_fn'](sys.argv[1]+'/f.o',g['KEEP'])
spe=R.spills(sys.argv[1]+'/pei.mir')
def vote(a_b,b_b,spb):
    ai=R.ins(a_b); bi=R.ins(b_b)
    sm=difflib.SequenceMatcher(None,g['mask'](R.fmask(a_b)),g['mask'](R.fmask(b_b)),autojunk=False)
    V={}
    for a,c,n in sm.get_matching_blocks():
        for k in range(n):
            x=R.memoff(a_b,ai[a+k][0]); y=R.memoff(b_b,bi[c+k][0])
            if y in spb and x is not None: V.setdefault(y,{}); V[y][x]=V[y].get(x,0)+1
    return V
V=vote(mb,eb,spe)
undo={y:max(d,key=d.get) for y,d in V.items()}
# targets collide? find e1 slots with no unique main image
import collections
cnt=collections.Counter(undo.values())
print('collisions',{k:v for k,v in cnt.items() if v>1})
for y in sorted(spe,reverse=True)[:16]: print(y,V.get(y))
VO=vote(R.ORIG,eb,spe)
for y in (-2304,-2392,-2384,-2328): print('orig votes',y,VO.get(y))
mp=dict(undo); mp[-2304]=-2384; mp[-2392]=-3128
assert len(set(mp.values()))==len(mp) and set(mp.values())==spe, (len(set(mp.values())), set(mp.values())^spe)
b1=R.apply(eb,mp); print('J1 holder->-2384, clonerun->-3128: M',R.M(b1),'ratio',R.ratio(b1))
mp0=dict(undo); mp0[-2304]=-3128; b0=R.apply(eb,mp0); print('J0 undo shift, holder->bottom: M',R.M(b0))
mpm=dict(undo); mpm[-2304]=-2384; mpm[-2392]=-2304 if False else -3128
# try clone-run at every slot (swap with occupant)
best=None
inv={v:k for k,v in mp.items()}
res=[]
for s in sorted(spe):
    if s in (-2384,): continue
    m2=dict(mp); a=inv[s]; m2[-2392]=s; m2[a]=-3128
    res.append((R.M(R.apply(eb,m2)),s))
res.sort(reverse=True); print('clonerun swap best',res[:6])
mb2,pm=R.bestperm(eb,spe,3); print('e1 perm bound',mb2)
mbm,_=R.bestperm(b1,spe,3); print('J1 then perm bound',mbm)
