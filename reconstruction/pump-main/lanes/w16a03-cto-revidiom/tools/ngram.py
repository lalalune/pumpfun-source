"""Reverse idiom index: alpha-renamed shape n-grams over every matched original window; per orig-only admin_cto run, list
the matched windows that contain the same shapes (with the run's matched neighbours as context)."""
import sys,os,json,collections,pickle
sys.path.insert(0,os.path.dirname(__file__))
import shape,runs
from win_dm import dm
CTO=0x22a10
def build(n,kw):
    o=shape.orig(); ws=shape.windows()
    idx=collections.defaultdict(list)
    # map instruction index -> window
    starts=[w[0] for w in ws]; import bisect
    wi=[None]*len(o)
    for i,(a,t,p) in enumerate(o):
        j=bisect.bisect_right(starts,a)-1
        if j>=0 and a<ws[j][0]+ws[j][1]: wi[i]=ws[j][0]
    for i in range(len(o)-n+1):
        w=wi[i]
        if w is None or w==CTO or wi[i+n-1]!=w: continue
        key=shape.shape_seq([o[k][2] for k in range(i,i+n)],**kw)
        idx[key].append((w,o[i][0]-w))
    return idx
if __name__=='__main__':
    n=int(sys.argv[1]) if len(sys.argv)>1 else 5
    keep_off = (sys.argv[2]!='nooff') if len(sys.argv)>2 else True
    kw=dict(keep_off=keep_off)
    cache=f'{shape.OUT}/idx_n{n}_{int(keep_off)}.pkl'
    if os.path.exists(cache): idx=pickle.load(open(cache,'rb'))
    else: idx=build(n,kw); pickle.dump(dict(idx),open(cache,'wb'))
    O=runs.cto_insns('orig'); d=json.load(open(shape.OUT+'/runs_main.json')); R=d['runs']
    names={w[0]:(w[2][0] if w[2] else '?') for w in shape.windows()}
    minlen=int(sys.argv[3]) if len(sys.argv)>3 else 2
    for i,j in R:
        if j-i<minlen: continue
        lo=max(0,i-2); hi=min(len(O),j+2)
        seq=[O[k][2] for k in range(lo,hi)]
        hits=collections.Counter(); where=collections.defaultdict(list); nk=0; covered=0
        for s in range(0,len(seq)-n+1):
            # only n-grams that include at least one run instruction
            if s+n-1 < i-lo or s > j-1-lo: continue
            nk+=1
            key=shape.shape_seq(seq[s:s+n],**kw)
            L=idx.get(key,[])
            if L: covered+=1
            for w,off in set(L):
                hits[w]+=1; where[w].append(off)
        print(f'=== run {O[i][0]:#06x}-{O[j-1][0]:#06x} ({j-i} insns) {n}-grams {nk}, found anywhere {covered}')
        for w,c in hits.most_common(6):
            offs=sorted(set(where[w]))
            print(f'     {c:3d}/{nk}  {w:#08x} {dm(names.get(w,"?"))[:90]}  @+{",".join(hex(x) for x in offs[:4])}')
