import sys
src,dst,a,b=sys.argv[1:5]; t=open(src).read()
x='br i1 %or.cond.not.i, label %bb76, label %bb66.i'; assert t.count(x)==1
t=t.replace(x,x+', !prof !99990'); t+='\n!99990 = !{!"branch_weights", i32 %s, i32 %s}\n'%(a,b); open(dst,'w').write(t)
