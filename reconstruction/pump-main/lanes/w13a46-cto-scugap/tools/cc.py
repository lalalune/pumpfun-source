#!/usr/bin/env python3
"""cc.py <a.so> <b.so>: diff two admin_cto candidates (token stream), show non-equal runs with disasm."""
import sys, difflib
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a46-cto-scugap/tools')
from census import cand_tok, dis
a,b=sys.argv[1],sys.argv[2]
ta,sa,na=cand_tok(a); tb,sb,nb=cand_tok(b)
da=dis(a,sa,na); db=dis(b,sb,nb)
sm=difflib.SequenceMatcher(None,[x[2] for x in ta],[x[2] for x in tb],autojunk=False)
print('ratio',round(sm.ratio(),5),len(ta),len(tb))
for t,i1,i2,j1,j2 in sm.get_opcodes():
    if t=='equal': continue
    print(f'--{t} a[{i1}:{i2}] b[{j1}:{j2}]')
    for k in range(i1,i2): print('   A',hex(ta[k][0]-sa),da.get(ta[k][0],'?'))
    for k in range(j1,j2): print('   B',hex(tb[k][0]-sb),db.get(tb[k][0],'?'))
