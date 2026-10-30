import sys,importlib.util
spec=importlib.util.spec_from_file_location('c2','/dev/null')
import re,collections
def load(p):
    ch=[];cur=[]
    for l in open(p):
        l=l.rstrip('\n')
        if not l.strip(): continue
        a,rest=l.split(None,1)
        if ' call ' in ' '+rest:
            lab=rest.split(';')[-1].strip()[:40] if ';' in rest else 'X'
            cur.append(1); ch.append((lab,int(a,16),len(cur))); cur=[]
        elif rest.strip()=='exit': cur.append(1); ch.append(('exit',int(a,16),len(cur))); cur=[]
        else: cur.append(1)
    occ=collections.Counter(); out={}; order=[]
    for lab,a,n in ch:
        occ[lab]+=1; out[(lab,occ[lab])]=(a,n); order.append((lab,occ[lab]))
    return out,order
o,oo=load(sys.argv[1]); cs=[load(p)[0] for p in sys.argv[2:]]
tot=[0]*len(cs)
for k in oo:
    a,n=o[k]; ds=[]
    for i,c in enumerate(cs):
        m=c.get(k); d=(m[1]-n) if m else -n; tot[i]+=d; ds.append(d)
    if any(ds): print(f'{a:#06x} {n:4d} {k[0][:38]:38s}#{k[1]:<2d} '+' '.join(f'{d:+5d}' for d in ds))
print('total insn delta',tot)
