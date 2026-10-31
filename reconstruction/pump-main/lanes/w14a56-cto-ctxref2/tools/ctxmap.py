#!/usr/bin/env python3
"""ctxmap.py <listing from lst.py>: ctx pointer spill slot (entry store of r2) and every reload of it with the field loads that follow (+8 accounts, +35 creator_vault bump, +39 pool_authority bump, +46 event_authority bump)."""
import sys
L=[l.split() for l in open(sys.argv[1]) if l[0]!=' ']
slot=[int(l[4]) for l in L[:6] if l[1]=='7b' and l[3]=='2'][0]
print('ctx slot',slot)
for i,l in enumerate(L):
    if l[1]=='79' and l[3]=='10' and int(l[4])==slot:
        r=l[2]; nxt=[x for x in L[i+1:i+12] if x[3]==r and x[1] in('71','79','bf','07')]
        print(l[0],'reload ctx ->r'+r, ' uses:',[(x[0],x[1],'r'+x[2],x[4]) for x in nxt[:3]])
