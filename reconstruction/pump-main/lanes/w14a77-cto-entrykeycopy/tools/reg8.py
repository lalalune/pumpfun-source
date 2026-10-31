#!/usr/bin/env python3
"""reg8.py <m.o>...: per-0x800 orig region counts of matched orig instrs under global alignment: exact / fm / rm."""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(__file__))
from slots import orig_dis,cand_dis
from abs import n1,n2
o=orig_dis(); W=0x800; NB=o[-1][0]//W+1
def ex(s):
    import re
    if s.startswith('call'): return 'call'
    s=re.sub(r'^lddw (r\d+), .*',r'lddw \1',s)
    return s
for p in sys.argv[1:]:
    c=cand_dis(p); row=[p.split('/')[-2]]
    for f in (ex,n1,n2):
        sm=difflib.SequenceMatcher(None,[f(t) for _,t in o],[f(t) for _,t in c],autojunk=False)
        cnt=[0]*NB
        for a,b,n in sm.get_matching_blocks():
            for k in range(n): cnt[o[a+k][0]//W]+=1
        row.append(' '.join('%3d'%x for x in cnt)+' |%4d'%sum(cnt))
    print(row[0]); print('  ex',row[1]); print('  fm',row[2]); print('  rm',row[3])
