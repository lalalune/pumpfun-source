#!/usr/bin/env python3
"""bw.py in.ll out.ll 'br-line-substring' W1 W2 : attach !prof branch_weights W1,W2 to the unique br matching. Oracle only."""
import sys
src,dst,pat,w1,w2=sys.argv[1:6]; t=open(src).read()
assert t.count(pat)==1,t.count(pat)
i=t.index(pat); e=t.index('\n',i); line=t[i:e]
if '!prof' in line: line=line[:line.index(', !prof')]
t=t[:i]+line+f', !prof !{{!"branch_weights", i32 {w1}, i32 {w2}}}'+t[e:]
open(dst,'w').write(t)
