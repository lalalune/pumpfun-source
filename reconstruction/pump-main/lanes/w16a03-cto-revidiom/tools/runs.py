"""orig-only runs of admin_cto (true LCS on rfj-masked tokens) vs a candidate disassembly (main.dis or a fn.bin)."""
import sys,os,re,json,pickle
sys.path.insert(0,os.path.dirname(__file__))
import shape
CTO=0x22a10; N=27400
def tok_rfj(p):
    mn,ops=p; s=[]
    for o in ops:
        if o[0]=='r': s.append('fp' if o[1]==10 else 'R')
        elif o[0]=='m': s.append('[fp]' if o[1]==10 else f'[R{o[2]:+#x}]')
        elif o[0]=='i': s.append('fn' if mn=='call' else f'{o[1]:#x}')
        elif o[0]=='j': s.append('@')
        else: s.append('?')
    return mn+' '+','.join(s)
def matched(A,B):
    n,k=len(A),len(B); L=[[0]*(k+1) for _ in range(n+1)]
    for i in range(n-1,-1,-1):
        Li=L[i]; L1=L[i+1]; x=A[i]
        for j in range(k-1,-1,-1):
            Li[j]=L1[j+1]+1 if x==B[j] else (L1[j] if L1[j]>Li[j+1] else Li[j+1])
    h=[None]*n; i=j=0
    while i<n and j<k:
        if A[i]==B[j] and L[i][j]==L[i+1][j+1]+1: h[i]=j; i+=1; j+=1
        elif L[i+1][j]>=L[i][j+1]: i+=1
        else: j+=1
    return h
def cto_insns(which='orig'):
    if which=='orig': rows=shape.orig()
    else: rows=shape.main()[0]
    return [(a-CTO,t,p) for a,t,p in rows if CTO<=a<CTO+N]
if __name__=='__main__':
    O=cto_insns('orig'); M=cto_insns('main')
    cache=shape.OUT+'/runs_main.pkl'
    if os.path.exists(cache): h=pickle.load(open(cache,'rb'))
    else:
        h=matched([tok_rfj(p) for a,t,p in O],[tok_rfj(p) for a,t,p in M]); pickle.dump(h,open(cache,'wb'))
    print('orig',len(O),'main',len(M),'matched',sum(1 for x in h if x is not None))
    # runs
    runs=[]; i=0
    while i<len(O):
        if h[i] is None:
            j=i
            while j<len(O) and h[j] is None: j+=1
            runs.append((i,j)); i=j
        else: i+=1
    json.dump({'h':h,'runs':runs},open(shape.OUT+'/runs_main.json','w'))
    L=[j-i for i,j in runs]
    print('runs',len(runs),'insns',sum(L),'len>=3',sum(1 for x in L if x>=3),'insns in len>=3',sum(x for x in L if x>=3))
