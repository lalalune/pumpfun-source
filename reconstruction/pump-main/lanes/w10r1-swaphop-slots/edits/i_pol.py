def edit(t):
    a = "  %switch232 = icmp eq i64 %_1130.sroa.0.0, 1\n  br i1 %switch232, label %bb159, label %bb172\n"
    assert t.count(a) == 1
    return t.replace(a, "  %switch232 = icmp eq i64 %_1130.sroa.0.0, 0\n  br i1 %switch232, label %bb172, label %bb159\n")
