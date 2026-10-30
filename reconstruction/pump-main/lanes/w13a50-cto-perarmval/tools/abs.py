#!/usr/bin/env python3
"""abs.py <m.o|so>...: abstracted ratios vs original: fm (frame offsets masked), rm (regs+frame masked)."""
import sys,re,difflib,os
sys.path.insert(0,os.path.dirname(__file__))
from slots import orig_dis,cand_dis
def n1(s):
    if s.startswith('call'): return 'call'
    s=re.sub(r'^lddw (r\d+), .*',r'lddw \1',s)
    if s.startswith('j'): s=re.sub(r'([+-]0x[0-9a-f]+|[+-]\d+)$','J',s)
    return re.sub(r'r10 - 0x[0-9a-f]+','r10-X',s)
def n2(s): return re.sub(r'\br\d\b','r',n1(s))
if __name__=="__main__":
  o=[t for _,t in orig_dis()]
  for p in sys.argv[1:]:
      c=[t for _,t in cand_dis(p)]
      r=[]
      for f in (n1,n2):
          sm=difflib.SequenceMatcher(None,[f(t) for t in o],[f(t) for t in c],autojunk=False); r.append(round(sm.ratio(),5))
      print(p.split('/')[-2], len(c)*8, 'fm',r[0],'rm',r[1])
