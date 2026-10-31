#!/usr/bin/env python3
"""mc.py name...: M (matched masked tokens), bytes, slots for rx/<name>/fn.bin"""
import sys,os,difflib
D=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/'
A=sys.argv[1:]; sys.argv=['x','n']
exec(open(D+'tools/rx.py').read().split('OUT=os.environ')[0])
o=mask(orig_window())
for n in A:
    p=D+'rx/'+n+'/fn.bin'
    if not os.path.exists(p): print(n,'missing'); continue
    raw=open(p,'rb').read(); c=mask(raw)
    M=sum(b.size for b in difflib.SequenceMatcher(None,o,c,autojunk=False).get_matching_blocks())
    ob=b''.join(o); cb=b''.join(c)
    sd=sum(1 for i in range(0,len(ob),8) if ob[i:i+8]!=cb[i:i+8]) if len(ob)==len(cb) else None
    print('%-16s M %d bytes %d (%+d) slots %s ntok %d'%(n,M,len(raw),len(raw)-27400,sd,len(c)))
