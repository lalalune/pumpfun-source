#!/usr/bin/env python3
"""revidiom.py: reverse idiom lookup for admin_cto (0x22a10) instruction shapes.

  revidiom.py range <lo> <hi> [--n 4] [--top 4]   orig admin_cto offsets [lo,hi)
  revidiom.py runs [--min 3] [--n 4]                every orig-only run (true LCS, rfj mask, vs main)

Shapes: opcode + operands with registers alpha-renamed inside the n-gram (dataflow kept), r10 offsets and
immediates masked (except and/shift masks and |imm|<4 compare constants), non-r10 memory offsets kept.
For each n-gram of the range, finds every matched original window (all 1,034 except admin_cto) with the same
shape, ranks windows by how many of the range's n-grams they contain, prefers rare n-grams (<= 8 windows),
and maps each hit to source through the line-table build (srcmap.py: innermost .loc and the nearest
programs/ call-site .loc). Pure Python, no build slot after the one-time line-table build.
"""
import sys,os,collections,pickle,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import shape,runs,srcmap
from win_dm import dm
CTO=0x22a10
def index(n):
    cache=f'{shape.OUT}/idx_n{n}_1.pkl'
    if os.path.exists(cache): return pickle.load(open(cache,'rb'))
    import ngram
    idx=ngram.build(n,dict(keep_off=True)); idx=dict(idx); pickle.dump(idx,open(cache,'wb')); return idx
def lookup(lo,hi,n=4,top=4,rare=8,out=sys.stdout):
    O=runs.cto_insns('orig'); idx=index(n)
    names={w[0]:(w[2][0] if w[2] else 'admin_cto') for w in shape.windows()}
    sel=[k for k,(a,t,p) in enumerate(O) if lo<=a<hi]
    if not sel: return
    i0=max(0,sel[0]-(n-1)); i1=min(len(O),sel[-1]+n)
    seq=O[i0:i1]
    per_w=collections.defaultdict(list); grams=[]
    for s in range(len(seq)-n+1):
        if seq[s+n-1][0]<lo or seq[s][0]>=hi: continue
        key=shape.shape_seq([x[2] for x in seq[s:s+n]],keep_off=True)
        L=idx.get(key,[]); wset={w for w,o in L}
        grams.append((seq[s][0],key,len(wset)))
        for w,off in L: per_w[w].append((seq[s][0],off,len(wset)))
    print(f'### orig {lo:#06x}-{hi:#06x}: {len(grams)} {n}-grams, {sum(1 for g in grams if g[2]==0)} unseen in the matched corpus, {sum(1 for g in grams if 0<g[2]<=rare)} rare (<= {rare} windows)',file=out)
    for a,key,c in grams:
        if c==0: print(f'    unseen @{a:#06x}: {" ; ".join(key)}',file=out)
    def score(w):
        v=per_w[w]; return (len({a for a,o,c in v if c<=rare}), len({a for a,o,c in v}))
    for w in sorted(per_w,key=score,reverse=True)[:top]:
        r,tot=score(w)
        v=sorted(per_w[w],key=lambda x:x[2])
        a,off,c=v[0]
        loc=srcmap.loc(w+off); u=srcmap.userloc(w+off)
        inner=f'{loc[1].split("/")[-1]}:{loc[2]}' if loc and loc[1] else '?'
        snip=''
        if u:
            line=srcmap.srcline(u[0],u[1]); snip=line[max(0,u[2]-1):u[2]+110].strip()
        print(f'    {w:#08x} {dm(names[w])[:70]:70s} grams {tot} (rare {r}); best @cto{a:#06x}=win+{off:#x} [{c} wins] inner {inner}; user {u[0].split("/")[-1]+":"+str(u[1]) if u else "?"}  {snip[:110]}',file=out)
if __name__=='__main__':
    a=sys.argv[1:]; n=4; top=4; mn=3
    if '--n' in a: i=a.index('--n'); n=int(a[i+1]); del a[i:i+2]
    if '--top' in a: i=a.index('--top'); top=int(a[i+1]); del a[i:i+2]
    if '--min' in a: i=a.index('--min'); mn=int(a[i+1]); del a[i:i+2]
    if a[0]=='range': lookup(int(a[1],16),int(a[2],16),n,top)
    elif a[0]=='runs':
        O=runs.cto_insns('orig'); d=json.load(open(shape.OUT+'/runs_main.json'))
        for i,j in d['runs']:
            if j-i>=mn: lookup(O[i][0],O[j-1][0]+8,n,top)
