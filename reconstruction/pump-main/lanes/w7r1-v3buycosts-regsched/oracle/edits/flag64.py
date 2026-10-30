import re,os
MODE=os.environ.get('FM','ne')
def edit(f):
    L=f.split('\n')
    for i,l in enumerate(L):
        if l.startswith('  %5 = phi i1'):
            s=l.replace('%5 = phi i1','%f64 = phi i64')
            if MODE=='ne': s=s.replace('[ false,','[ 0,').replace('[ true,','[ 1,')
            else: s=s.replace('[ false,','[ 1,').replace('[ true,','[ 0,')
            L[i]=s
            j=i
    # insert icmp at first non-phi position of bb6
    k=j
    while L[k+1].startswith('  %') and ' = phi ' in L[k+1]: k+=1
    L.insert(k+1,'  %%5 = icmp %s i64 %%f64, 0'%('ne' if MODE=='ne' else 'eq'))
    return '\n'.join(L)
