import runpy,re
base=runpy.run_path('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w3-sellv3-oracle/edits/ir_norecheck.py')['edit']
def swapphis(f,a,b):
    L=f.split('\n')
    ia=next(i for i,l in enumerate(L) if l.lstrip().startswith(a+' = phi'))
    ib=next(i for i,l in enumerate(L) if l.lstrip().startswith(b+' = phi'))
    L[ia],L[ib]=L[ib],L[ia]; return '\n'.join(L)
def edit(f):
    f=base(f)
    import os
    for pair in os.environ.get('PAIRS','').split(';'):
        if pair: a,b=pair.split(','); f=swapphis(f,a,b)
    return f
