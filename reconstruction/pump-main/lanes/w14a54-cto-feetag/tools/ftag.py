#!/usr/bin/env python3
"""ftag.py in.ll out.ll [TY] : add a fee-tag phi of constants in bb76 (1 from bb58.i, 0 from the fee-None exits) and use it
for the line-757 fee store test (%switch48) instead of the fee argument's tag. Oracle only."""
import sys,re
src,dst=sys.argv[1:3]; ty=sys.argv[3] if len(sys.argv)>3 else 'i64'
t=open(src).read()
i=t.index('\nbb76:'); e=t.index('\n',i+1)
preds=re.search(r'; preds = (.*)',t[i:e]).group(1).replace('%','').split(', ')
inc=', '.join(f'[ {1 if p.startswith("bb58.i") or p.startswith("bb76.sbb58") else 0}, %{p} ]' for p in preds)
t=t[:e+1]+f'  %ftag = phi {ty} {inc}\n'+t[e+1:]
if ty=='i64': t=t.replace('%switch48 = icmp eq i64 %0, 1','%switch48 = icmp eq i64 %ftag, 1')
else: t=t.replace('%switch48 = icmp eq i64 %0, 1','%switch48 = icmp ne i8 %ftag, 0')
open(dst,'w').write(t)
