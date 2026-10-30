import os
M=os.environ.get('E5','h')
H='%_0.sroa.0.0.off0.i70'
def edit(f):
    a='  %_504.sroa.0.0.off0 = phi i1 [ false, %bb18 ], [ false, %bb19 ], [ false, %bb20 ], [ true, %bb16 ]\n'; assert f.count(a)==1
    ph='  %hphi = phi i1 [ false, %bb18 ], [ '+H+', %bb19 ], [ '+H+', %bb20 ], [ true, %bb16 ]\n'
    if 'c' in M: ph+='  %cphi = phi i1 [ %_40.not, %bb18 ], [ %cashback.sroa.0.0.off0, %bb19 ], [ %cashback.sroa.0.0.off0, %bb20 ], [ false, %bb16 ]\n'
    f=f.replace(a,a+ph)
    c='  %571 = zext i1 '+H+' to i8\n'; assert f.count(c)==1
    f=f.replace(c,'  %571 = zext i1 %hphi to i8\n')
    if 'c' in M:
        x='zext i1 %cashback.sroa.0.0.off0 to i8'; assert f.count(x)==1, f.count(x)
        f=f.replace(x,'zext i1 %cphi to i8')
    if 'p' in M:
        d='%_185 = icmp ne i8 %683, 0'; assert f.count(d)==1
        f=f.replace(d,'%_185 = icmp ne i8 %571, 0')
    return f
