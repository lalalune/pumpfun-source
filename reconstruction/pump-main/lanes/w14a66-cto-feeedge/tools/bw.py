#!/usr/bin/env python3
"""bw.py in.ll out.ll BLOCK T F : put !prof branch_weights T,F on BLOCK's conditional br. Oracle only."""
import sys
src,dst,b,T,F=sys.argv[1:6]; t=open(src).read()
k=t.index('\n'+b+':'); e=t.index('\n\n',k+1); x=t[k:e]; L=x.split('\n'); i=[j for j,l in enumerate(L) if l.strip().startswith('br i1')][-1]
L[i]=L[i]+', !prof !999990'; t=t[:k]+'\n'.join(L)+t[e:]
t+='\n!999990 = !{!"branch_weights", i32 %s, i32 %s}\n'%(T,F)
open(dst,'w').write(t)
