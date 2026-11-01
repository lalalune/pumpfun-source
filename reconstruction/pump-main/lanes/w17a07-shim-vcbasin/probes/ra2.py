# accounts pointer re-derived (volatile ctx.accounts) at the sweep entry AND at the post-sweep join, so the entry value dies before the sweep
import re,os
V=os.environ.get('RA_V','_281'); B1=os.environ.get('RA_BB','bb84'); B2=os.environ.get('RA_BB2','bb89')
def f(t):
    L=t.split('\n')
    i=[k for k,l in enumerate(L) if l.startswith(B1+':')][0]
    x=[k for k,l in enumerate(L) if '5sweep17h' in l and l.split(':')[0].endswith('.exit')][0]
    j=[k for k,l in enumerate(L) if l.startswith(B2+':')][0]
    e=i+next(k for k,l in enumerate(L[i:]) if l=='}')
    for k in range(i+1,x): L[k]=re.sub(r'%'+V+r'\b','%acc2',L[k])
    for k in range(j+1,e): L[k]=re.sub(r'%'+V+r'\b','%acc3',L[k])
    jj=j+1
    while L[jj].lstrip().startswith('%') and ' = phi ' in L[jj]: jj+=1
    L.insert(jj,'  %acc3 = load volatile ptr, ptr %3, align 8, !nonnull !2, !align !3, !noundef !2')
    L.insert(i+1,'  %acc2 = load volatile ptr, ptr %3, align 8, !nonnull !2, !align !3, !noundef !2')
    return '\n'.join(L)
EDITS=[f]
