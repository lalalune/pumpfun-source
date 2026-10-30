# sweep gate as a skip-polarity phi of constants: br skip -> post (bb82), else sweep (bb77) (orig 0x1d40 jne skip,0 -> 0x3c68)
def edit(f):
    a='  %_504.sroa.0.0.off0 = phi i1 [ false, %bb18 ], [ false, %bb19 ], [ false, %bb20 ], [ true, %bb16 ]\n'; assert f.count(a)==1
    f=f.replace(a,'  %skipg = phi i1 [ true, %bb18 ], [ true, %bb19 ], [ true, %bb20 ], [ false, %bb16 ]\n')
    b='  br i1 %_504.sroa.0.0.off0, label %bb77, label %bb82\n'; assert f.count(b)==1
    return f.replace(b,'  br i1 %skipg, label %bb82, label %bb77\n')
