import sys,re,itertools; sys.path.insert(0,'.'); import irlib
t,m=irlib.load(); f0=m.group(0)
lines=f0.split('\n'); al=[i for i,l in enumerate(lines) if ' = alloca ' in l]
print(len(al),'allocas')
for i,j in itertools.combinations(range(len(al)),2):
    L=lines[:]; L[al[i]],L[al[j]]=L[al[j]],L[al[i]]
    r,d=irlib.run('\n'.join(L))
    print(r, lines[al[i]].split('=')[0].strip(), '<->', lines[al[j]].split('=')[0].strip())
