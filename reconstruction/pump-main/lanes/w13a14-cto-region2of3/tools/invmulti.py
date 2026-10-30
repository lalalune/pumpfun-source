"""invmulti.py: edit for ctoracle run: env INV="k1,k2,.." inverts those br lines (indices in execute's text lines)."""
import os,re
BR=re.compile(r'^(\s*)br i1 (%[\w.$"]+), label (%[\w.$"]+), label (%[\w.$"]+)(.*)$')
def edit(f):
    L=f.split('\n')
    for k in map(int,os.environ['INV'].split(',')):
        m=BR.match(L[k]); ind,c,a,b,rest=m.groups()
        rest=re.sub(r', !prof !\d+','',rest)
        L[k]=f'{ind}%inv{k} = xor i1 {c}, true\n{ind}br i1 %inv{k}, label {b}, label {a}{rest}'
    return '\n'.join(L)
