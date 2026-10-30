#!/usr/bin/env python3
"""pbk.py name1 name2..: plain (exact-text, call/lddw imms masked) global alignment, matched orig insns per 0x800 orig region."""
import sys,os,re,difflib
sys.path.insert(0,os.path.dirname(__file__))
from slots import orig_dis,cand_dis
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def norm(t):
    t=re.sub(r'^(call) .*','call',t); t=re.sub(r'^(lddw r\d+), .*',r'\1',t); t=re.sub(r'^(j\w+ .*?)[+-](0x[0-9a-f]+|\d+)$',r'\1J',t); t=re.sub(r'^ja .*','ja',t)
    return t
if __name__=='__main__':
    od=orig_dis(); ot=[norm(t) for _,t in od]
    cols=[]
    for n in sys.argv[1:]:
        cd=cand_dis(O+'/rx/%s/m.o'%n); ct=[norm(t) for _,t in cd]
        sm=difflib.SequenceMatcher(None,ot,ct,autojunk=False); m=set()
        for a,b,s in sm.get_matching_blocks():
            for i in range(s): m.add(od[a+i][0])
        cols.append(m)
    print('reg   '+' '.join('%8s'%n[:8] for n in sys.argv[1:]))
    for b in range(0,0x6b00,0x800):
        print('%5x '%b+' '.join('%8d'%sum(1 for a in c if b<=a<b+0x800) for c in cols))
    print('total '+' '.join('%8d'%len(c) for c in cols))
