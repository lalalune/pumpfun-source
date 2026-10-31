# tag (%_539.sroa.0.0) spilled only across wallet(): stored at wallet entry (bb33), reloaded in the two wallet exits, phi at bb35
X='_ZN14pump_recovered9admin_cto7execute6wallet17h67aeb09bf4f58cf9E'
def f(t):
    t=t.replace("start:\n","start:\n  %tagsl = alloca i8, align 1\n",1)
    a="bb33:                                             ; preds = %bb28\n"; assert t.count(a)==1
    t=t.replace(a,a+"  store i8 %_539.sroa.0.0, ptr %tagsl, align 1\n")
    a=X+".exit.thread: ; preds = %bb44.i77, %bb43.i, %bb3.i69, %bb59.i71, %bb1.i\n"; assert t.count(a)==1
    t=t.replace(a,a+"  %tw1 = load i8, ptr %tagsl, align 1\n")
    a="  %318 = icmp eq i64 %_0.sroa.0.4.i, 2\n"; assert t.count(a)==1
    t=t.replace(a,"  %tw2 = load i8, ptr %tagsl, align 1\n"+a)
    a="bb35:                                             ; preds = %"+X+".exit.thread, %"+X+".exit, %bb28\n"; assert t.count(a)==1
    t=t.replace(a,a+"  %tagj = phi i8 [ %tw1, %"+X+".exit.thread ], [ %tw2, %"+X+".exit ], [ %_539.sroa.0.0, %bb28 ]\n")
    for a,b in [("  %577 = icmp ne i8 %_539.sroa.0.0, 2","  %577 = icmp ne i8 %tagj, 2"),("  store i8 %_539.sroa.0.0, ptr %val6, align 1","  store i8 %tagj, ptr %val6, align 1")]:
        assert t.count(a)==1; t=t.replace(a,b)
    return t
EDITS=[f]
