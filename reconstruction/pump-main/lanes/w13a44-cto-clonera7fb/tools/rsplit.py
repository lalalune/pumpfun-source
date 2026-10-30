#!/usr/bin/env python3
"""rsplit.py <ra.log> <vreg>: per-physreg global-split candidates (static/total cost, bundles) of the RS_Split round of %vreg."""
import sys,re
L=open(sys.argv[1]).read().split('\n'); v='selectOrSplit GPR:%'+sys.argv[2]+' '
i=0
while i<len(L):
    if L[i].startswith(v):
        j=i; blk=[]
        while j<len(L) and L[j]!='': blk.append(L[j]); j+=1
        if any(x.startswith('RS_Split') for x in blk):
            for l in blk:
                if l.startswith('$r'):
                    b=re.findall(r'EB#(\d+)',l); st=re.search(r'static = ([\d.e-]+)',l); tot=re.search(r'total = ([\d.e-]+)',l)
                    print(l.split()[0], st.group(1) if st else l[4:60], tot.group(1) if tot else '-', len(b), ' '.join(b))
                elif l.startswith('Split for') or l.startswith('Compact'): print(l[:200])
            break
        i=j
    i+=1
