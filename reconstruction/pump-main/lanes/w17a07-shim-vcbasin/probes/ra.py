# sweep re-derives the accounts pointer with a volatile load of ctx.accounts at the sweep entry (bb83)
import re,os
LO=int(os.environ.get('RA_LO','0')); HI=int(os.environ.get('RA_HI','0')); BB=os.environ.get('RA_BB','bb83')
def f(t):
    L=t.split('\n')
    i=[k for k,l in enumerate(L) if l.startswith(BB+':')][0]
    lo=LO or i+1; hi=HI or [k for k,l in enumerate(L) if '5sweep17h' in l and l.split(':')[0].endswith('.exit')][0]
    for k in range(lo,hi):
        L[k]=re.sub(r'%'+os.environ.get('RA_V','_276')+r'\b','%acc2',L[k])
    L.insert(i+1,'  %acc2 = load '+os.environ.get('RA_VOL','volatile ')+'ptr, ptr %3, align 8, !nonnull !2, !align !3, !noundef !2')
    return '\n'.join(L)
EDITS=[f]
