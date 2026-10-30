#!/usr/bin/env python3
"""side.py <m.o> <orig_addr_hex> [before] [after]: orig vs candidate side by side around an orig address (rm alignment)."""
import sys,re,difflib,os;sys.path.insert(0,os.path.dirname(__file__))
from slots import orig_dis,cand_dis
from abs import n2
o=orig_dis(); c=cand_dis(sys.argv[1]); x=int(sys.argv[2],16); B=int(sys.argv[3]) if len(sys.argv)>3 else 6; A=int(sys.argv[4]) if len(sys.argv)>4 else 30
sm=difflib.SequenceMatcher(None,[n2(t) for _,t in o],[n2(t) for _,t in c],autojunk=False)
al={}
for a,b,n in sm.get_matching_blocks():
  for k in range(n): al[a+k]=b+k
i=min(k for k,(a,t) in enumerate(o) if a>=x and k in al); j=al[i]
for k in range(-B,A):
  print('%5x %-34s | %5x %s'%(o[i+k][0],o[i+k][1],c[j+k][0],c[j+k][1]))
