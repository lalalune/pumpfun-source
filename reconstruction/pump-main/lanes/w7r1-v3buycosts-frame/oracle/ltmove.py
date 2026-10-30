import sys,re,runpy; sys.path.insert(0,'.'); import irlib
from concurrent.futures import ThreadPoolExecutor
t,m=irlib.load(); f0=m.group(0)
import os
if os.environ.get('PRE'): f0=runpy.run_path(os.environ['PRE'])['edit'](f0)
L=f0.split('\n')
marks=[i for i,l in enumerate(L) if 'llvm.lifetime.' in l and l.strip().startswith('call')]
labs=[(i,re.match(r'("[^"]+"|[\w.$]+):',l).group(1)) for i,l in enumerate(L) if re.match(r'("[^"]+"|[\w.$]+):',l)]
starts=[0]+[i for i,_ in labs]  # line idx of label (0= define line, insert after 'start:')
start_lbl=L.index('start:')
targets=[]
for i,l in enumerate(L):
    if l=='start:' or re.match(r'("[^"]+"|[\w.$]+):',l): targets.append(('top',i))
    s=l.strip()
    if s.startswith(('br ','ret ','unreachable')): targets.append(('bot',i))
jobs=[]
for mi in marks:
    for kind,ti in targets:
        if kind=='top':
            ins=ti+1
            # skip allocas/phis
            while ' = alloca ' in L[ins] or ' phi ' in L[ins]: ins+=1
        else: ins=ti
        if ins in (mi,mi+1): continue
        N=L[:]; mk=N[mi]; N.insert(ins,mk); del N[mi if mi<ins else mi+1]
        jobs.append((mi,kind,ti,'\n'.join(N)))
def go(j):
    mi,kind,ti,f=j; r,d=irlib.run(f); return (r,mi,kind,ti)
with ThreadPoolExecutor(6) as ex: res=list(ex.map(go,jobs))
res=[x for x in res if x[0]]
res.sort(key=lambda x:x[0][1]+x[0][2])
print(len(jobs),'moves')
for r,mi,kind,ti in res[:25]: print(r, L[mi].strip()[:70], kind, L[ti][:60])
import collections; print(collections.Counter(r for r,*_ in res).most_common(12))
