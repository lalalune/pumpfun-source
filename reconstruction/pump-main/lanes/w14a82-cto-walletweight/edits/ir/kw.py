# sweep gate flag %_549 through an i8 slot across wallet() only: store at bb33 (wallet entry), reload at both wallet exits, phi at bb35
X='_ZN14pump_recovered9admin_cto7execute6wallet17h67aeb09bf4f58cf9E'
def f(t):
    t=t.replace("start:\n","start:\n  %kwsl = alloca i8, align 1\n",1)
    a="bb33:                                             ; preds = %bb28\n"; assert t.count(a)==1
    t=t.replace(a,a+"  %kwz = zext i1 %_549.sroa.0.0.off0 to i8\n  store i8 %kwz, ptr %kwsl, align 1\n")
    a=X+".exit.thread: ; preds = %bb44.i78, %bb43.i, %bb3.i69, %bb59.i72, %bb1.i\n"; assert t.count(a)==1
    t=t.replace(a,a+"  %kw1 = load i8, ptr %kwsl, align 1\n  %kw1b = trunc i8 %kw1 to i1\n")
    a="  %319 = icmp eq i64 %_0.sroa.0.4.i, 2\n"; assert t.count(a)==1
    t=t.replace(a,"  %kw2 = load i8, ptr %kwsl, align 1\n  %kw2b = trunc i8 %kw2 to i1\n"+a)
    a="  br i1 %_549.sroa.0.0.off0, label %bb84, label %bb89\n"; assert t.count(a)==1
    t=t.replace(a,"  %kwj = phi i1 [ %kw1b, %"+X+".exit.thread ], [ %kw2b, %"+X+".exit ], [ %_549.sroa.0.0.off0, %bb28 ]\n  br i1 %kwj, label %bb84, label %bb89\n")
    return t
EDITS=[f]
