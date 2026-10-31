# oracle: block early taildup of sweep exit with an empty asm (w14a06 e5) [+ optional weight on native zero edge]
import os
E='_ZN14pump_recovered9admin_cto7execute5sweep17h9943ff4781c7e018E.exit'
W=os.environ.get('W')
def f(t):
    x='  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_114.sroa.5.i)\n  %569 = icmp eq i64 %_415.sroa.0.3, 2\n'
    assert t.count(x)==1; t=t.replace(x,x.replace('\n  %569','\n  call void asm sideeffect "", ""()\n  %569',1))
    if W:
        y='  br i1 %_123.not.not.i, label %bb30.i, label %bb49.i\n'
        assert t.count(y)==1; t=t.replace(y,y[:-1]+', !prof !99999\n'); t+='\n!99999 = !{!"branch_weights", i32 %s, i32 %s}\n'%tuple(W.split(','))
    return t
EDITS=[f]
