# g1 on main 53abf28: skip-polarity gate phi, br skip -> post (bb81), sweep (bb76) fallthrough
def edit(f):
    a='  %_504.sroa.0.0.off0 = phi i1 [ false, %bb17 ], [ false, %bb18 ], [ false, %bb19 ], [ true, %bb15 ]\n'; assert f.count(a)==1
    f=f.replace(a,'  %skipg = phi i1 [ true, %bb17 ], [ true, %bb18 ], [ true, %bb19 ], [ false, %bb15 ]\n')
    b='  br i1 %_504.sroa.0.0.off0, label %bb76, label %bb81\n'; assert f.count(b)==1
    return f.replace(b,'  br i1 %skipg, label %bb81, label %bb76\n')
