#!/usr/bin/env python3
"""permb.py <cand> <orig_lo> <orig_hi> [--global] [--json out]: spill-slot permutation bound.
Skeleton-aligns cand vs the original, collects (cand frame off -> orig frame off) votes from aligned r10 dw accesses
whose orig offset lies in [lo,hi) (or everywhere with --global), builds a bijection sigma on the voted cand slots
(closing displaced slots onto vacated ones), applies sigma to EVERY r10 access of the function at exactly those offsets
and scores the rewritten blob (px2 score_bin: M, ratio, slots). Experiment only: prices a perfect spill colouring."""
import sys,os,difflib,struct,json,collections
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled,px2
a=sys.argv[1:]; p=a[0]; lo=int(a[1],16); hi=int(a[2],16); G='--global' in a
O=oracle.orig_window(); C=xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin')
ot,oo=xled.toks(O); ct,co=xled.toks(C); fa=xled.fmask(ot); fb=xled.fmask(ct)
def fr(t):
    """r10 frame access -> (off,size,kind) or None"""
    op=t[0]; cl=op&7; sz={0x18:8,0x10:2,0x08:1,0x00:4}.get(op&0x18)
    if cl==1 and (t[1]>>4)==10: return struct.unpack_from('<h',t,2)[0],sz,'ld'
    if cl in(2,3) and (t[1]&15)==10: return struct.unpack_from('<h',t,2)[0],sz,'st'
    return None
votes=collections.defaultdict(collections.Counter)
for tag,i1,i2,j1,j2 in difflib.SequenceMatcher(None,fa,fb,autojunk=False).get_opcodes():
    if tag!='equal': continue
    for k in range(i2-i1):
        i=i1+k; j=j1+k
        if not G and not(lo<=oo[i]<hi): continue
        x=fr(ot[i]); y=fr(ct[j])
        if x and y and x[1]==8 and y[1]==8: votes[y[0]][x[0]]+=1
# all cand frame accesses, to check slots are clean 8-byte dw slots
acc=collections.defaultdict(set)
for t in ct:
    f=fr(t)
    if f: acc[f[0]].add(f[1])
def clean(off):
    if acc.get(off)!={8}: return False
    return not any(o!=off and o<off+8 and o+max(s)>off for o,s in acc.items())
# greedy injective map by vote strength
sig={}; used=set()
for y,c in sorted(votes.items(),key=lambda kv:-kv[1].most_common(1)[0][1]):
    for x,n in c.most_common():
        if x not in used and clean(y) and (x==y or clean(x) or x not in acc):
            sig[y]=x; used.add(x); break
D=set(sig); Y=set(sig.values())
# close: slots in Y\D that cand uses must move to vacated D\Y
disp=sorted(y for y in Y-D if y in acc); free=sorted(D-Y)
bad=[y for y in disp if not clean(y)]
for y,f in zip(disp,free): sig[y]=f
if len(disp)>len(free): print('WARN unclosed',disp[len(free):],file=sys.stderr)
nonid={k:v for k,v in sig.items() if k!=v}
RW=[int(x,16) for x in a[a.index('--rw')+1].split(':')] if '--rw' in a else [0,1<<30]
out=bytearray(C); i=0; nrw=0
while i<len(C):
    n=16 if C[i]==0x18 else 8; t=C[i:i+n]; f=fr(t)
    if f and f[0] in sig and f[1]==8 and RW[0]<=i<RW[1]:
        struct.pack_into('<h',out,i+2,sig[f[0]]); nrw+=1
    i+=n
base=px2.score_bin(C); new=px2.score_bin(bytes(out))
res={'cand':p,'range':[hex(lo),hex(hi)],'global':G,'sigma':{hex(-k):hex(-v) for k,v in sorted(nonid.items())},
     'n_sigma':len(nonid),'rewrites':nrw,'unclean_displaced':[hex(-b) for b in bad],
     'base':{k:base[k] for k in('ratio','M','slots','bytes')},'perm':{k:new[k] for k in('ratio','M','slots','bytes')},
     'dM':new['M']-base['M'],'dch':{hex(k*0x400):new['ch'].get(k,0)-base['ch'].get(k,0) for k in sorted(set(new['ch'])|set(base['ch'])) if new['ch'].get(k,0)!=base['ch'].get(k,0)}}
if '--json' in a: open(a[a.index('--json')+1],'w').write(json.dumps(res,indent=1))
if '--bin' in a: open(a[a.index('--bin')+1],'wb').write(bytes(out))
print(json.dumps(res))
