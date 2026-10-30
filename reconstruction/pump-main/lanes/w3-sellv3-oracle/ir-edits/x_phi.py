import os
def swapphis(f,a,b):
    L=f.split('\n')
    ia=next(i for i,l in enumerate(L) if l.lstrip().startswith(a+' = phi'))
    ib=next(i for i,l in enumerate(L) if l.lstrip().startswith(b+' = phi'))
    L[ia],L[ib]=L[ib],L[ia]; return '\n'.join(L)
def edit(f):
    for pair in os.environ.get('PAIRS','%_0.sroa.25.0,%_0.sroa.0.0').split(';'):
        if pair: a,b=pair.split(','); f=swapphis(f,a,b)
    return f
