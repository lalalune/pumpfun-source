import sys,os
sys.path.insert(0,os.path.dirname(__file__))
import shape,runs
def tok(p,r,f,j):
    mn,ops=p; s=[]
    for o in ops:
        if o[0]=='r': s.append('fp' if o[1]==10 else (f'r{o[1]}' if r else 'R'))
        elif o[0]=='m':
            b='fp' if o[1]==10 else (f'r{o[1]}' if r else 'R')
            s.append(f'[{b}{o[2]:+#x}]' if (o[1]!=10 or f) else '[fp]')
        elif o[0]=='i': s.append('fn' if mn=='call' else f'{o[1]:#x}')
        elif o[0]=='j': s.append(f'{o[1]:+d}' if j else '@')
        else: s.append('?')
    return mn+' '+','.join(s)
def lcs(A,B):
    k=len(B); full=(1<<k)-1; M={}
    for j,y in enumerate(B): M[y]=M.get(y,0)|(1<<j)
    V=full
    for x in A:
        m=M.get(x)
        if m is None: continue
        U=V&m; V=((V+U)|(V-U))&full
    return k-bin(V).count('1')
O=runs.cto_insns('orig'); M=runs.cto_insns('main')
for r,f,j,name in [(1,1,1,'exact'),(1,1,0,'j-masked'),(0,1,0,'r,j masked'),(1,0,0,'f,j masked'),(0,0,0,'rfj masked')]:
    A=[tok(p,r,f,j) for a,t,p in O]; B=[tok(p,r,f,j) for a,t,p in M]
    print(f'{name:14s} LCS {lcs(A,B)} / {len(A)}')
