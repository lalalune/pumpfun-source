#!/usr/bin/env python3
"""applyws.py in.ll out.ll i:a:b [i:a:b ...] : add branch_weights to the i-th conditional br of execute."""
import sys,re
src=open(sys.argv[1]).read(); specs=[tuple(map(int,x.split(':'))) for x in sys.argv[3:]]
s=[m.start() for m in re.finditer(r'^define .*admin_cto7execute17h',src,re.M)][0]; e=src.index('\n}\n',s)
body=src[s:e]
lines=[(m.start(),m.group(0)) for m in re.finditer(r'^  br i1 [^\n]*$',body,re.M)]
md=[]; out=body
for k,(i,a,b) in sorted(enumerate(specs),key=lambda x:-lines[x[1][0]][0]):
    off,ln=lines[i]; tag='!%d'%(999900+k)
    out=out[:off]+ln+', !prof '+tag+out[off+len(ln):]
    md.append('%s = !{!"branch_weights", i32 %d, i32 %d}'%(tag,a,b))
open(sys.argv[2],'w').write(src[:s]+out+src[e:]+'\n'+'\n'.join(md)+'\n')
