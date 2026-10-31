# sweep gate flag %_549 through an i8 stack slot: stored at bb26, reloaded at bb35
def f(t):
    t=t.replace("start:\n","start:\n  %sksl = alloca i8, align 1\n",1)
    a="  %_549.sroa.0.0.off0 = phi i1 [ false, %bb21 ], [ false, %bb22 ], [ false, %bb23 ], [ true, %bb19 ]\n"; assert t.count(a)==1
    k=t.index(a)+len(a)
    while t[k:].startswith('  %') and ' = phi ' in t[k:t.index('\n',k)]: k=t.index('\n',k)+1
    t=t[:k]+"  %skz = zext i1 %_549.sroa.0.0.off0 to i8\n  store i8 %skz, ptr %sksl, align 1\n"+t[k:]
    a="  br i1 %_549.sroa.0.0.off0, label %bb84, label %bb89\n"; assert t.count(a)==1
    t=t.replace(a,"  %skl = load i8, ptr %sksl, align 1\n  %skb = trunc i8 %skl to i1\n  br i1 %skb, label %bb84, label %bb89\n")
    return t
EDITS=[f]
