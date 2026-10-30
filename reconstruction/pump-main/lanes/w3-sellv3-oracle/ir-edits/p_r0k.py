import os
def edit(f):
    a='  %_0 = alloca [16 x i8], align 8\n'
    L=f.split('\n'); i=L.index(a[:-1]); L.pop(i)
    k=int(os.environ['K']); L.insert(i-k,a[:-1])
    return '\n'.join(L)
