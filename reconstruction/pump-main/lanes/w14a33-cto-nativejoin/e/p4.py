import re
def f(t):
    t=t.replace("  %538 = icmp eq i64 %537, 2\n  br i1 %538, label %bb49.i, label %bb108.i","  %538 = icmp eq i64 %537, 2\n  br i1 %538, label %bb89, label %bb108.i")
    t=t.replace("[ %552, %bb92.i ], [ 2, %bb107.i ], ","[ %552, %bb92.i ], ")
    t=t.replace("[ %556, %bb92.i ], [ %_279.i, %bb107.i ], ","[ %556, %bb92.i ], ")
    t=t.replace("bb49.i:                                           ; preds = %bb86.i, %bb90.i126, %bb43.i120, %bb37.i117, %bb107.i, %bb92.i","bb49.i:                                           ; preds = %bb86.i, %bb90.i126, %bb43.i120, %bb37.i117, %bb92.i")
    m=re.search(r'(bb89:.*?\n  %_95\.sroa\.0\.0 = phi i64 \[ 0, %bb35 \], )',t)
    t=t.replace(m.group(1),m.group(1)+'[ %_279.i, %bb107.i ], ')
    return t
EDITS=[f]
