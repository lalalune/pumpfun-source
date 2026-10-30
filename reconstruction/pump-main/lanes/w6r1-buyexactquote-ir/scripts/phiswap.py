import os,re
# PS="bb113.i bb106.i": swap the two _0 phi lines in each named block (post-opt IR)
def edit(t):
    L=t.split('\n')
    s=next(i for i,l in enumerate(L) if l.startswith('define') and 'trade15buy_exact_quote17h' in l)
    e=next(i for i in range(s,len(L)) if L[i]=='}')
    for blk in os.environ['PS'].split():
        i=next(i for i in range(s,e) if L[i].startswith(blk))
        ph=[j for j in range(i+1,i+3) if '%_0.sroa' in L[j] and ' = phi ' in L[j]]
        assert len(ph)==2,(blk,ph)
        L[ph[0]],L[ph[1]]=L[ph[1]],L[ph[0]]
    return '\n'.join(L)
