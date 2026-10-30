import re,os
def edit(t):
    L=t.split('\n'); sel=os.environ.get('PS','4,12,5').split(',')
    for k in sel:
        i=next(i for i,l in enumerate(L) if l.startswith(f'  %_0.sroa.38.{k}.i = phi ptr'))
        assert L[i+1].startswith(f'  %_0.sroa.0.{k}.i = phi i64')
        L[i],L[i+1]=L[i+1],L[i]
    return '\n'.join(L)
