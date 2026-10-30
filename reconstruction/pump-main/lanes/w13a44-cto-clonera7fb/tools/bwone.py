#!/usr/bin/env python3
"""bwone.py <m.ll> <exact br line text> <a> <b> <out m.ll>: add branch_weights a:b to one br."""
import sys
m,br,a,b,out=sys.argv[1:6]
t=open(m).read(); line='  '+br.strip()+'\n'
assert t.count(line)==1,(t.count(line),line)
t=t.replace(line,'  '+br.strip()+', !prof !999991\n')+'\n!999991 = !{!"branch_weights", i32 %s, i32 %s}\n'%(a,b)
open(out,'w').write(t)
