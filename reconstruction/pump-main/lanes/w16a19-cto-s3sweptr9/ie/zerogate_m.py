# oracle on main m0n: gate polarity as the original (br skip -> join, else sweep): invert the !skip phi and swap the branch targets
import re
def f(t):
    a="  %_553.sroa.0.0.off0 = phi i1 [ false, %bb20 ], [ false, %bb21 ], [ false, %bb22 ], [ true, %bb18 ]\n"
    assert t.count(a)==1; t=t.replace(a,"  %_553.sroa.0.0.off0 = phi i1 [ true, %bb20 ], [ true, %bb21 ], [ true, %bb22 ], [ false, %bb18 ]\n")
    m=re.search(r"  br i1 %_553\.sroa\.0\.0\.off0, label %(\w+), label %(\w+)\n",t); assert m
    return t.replace(m.group(0),"  br i1 %%_553.sroa.0.0.off0, label %%%s, label %%%s\n"%(m.group(2),m.group(1)))
EDITS=[f]
