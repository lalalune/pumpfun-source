import os
MODE=os.environ.get('E4','full')
def edit(f):
    a='  %buf.i257 = alloca [24 x i8], align 8\n'; assert f.count(a)==1
    f=f.replace(a,a+'  %hslot = alloca [1 x i8], align 1\n')
    b='  %_0.sroa.0.0.off0.i45 = icmp ne i8 %42, 0\n'; assert f.count(b)==1
    f=f.replace(b,b+'  %hz0 = zext i1 %_0.sroa.0.0.off0.i45 to i8\n  store i8 %hz0, ptr %hslot, align 1\n')
    c='  %571 = zext i1 %_0.sroa.0.0.off0.i45 to i8\n'; assert f.count(c)==1
    f=f.replace(c,'  %571 = load i8, ptr %hslot, align 1\n')
    if MODE in('full','pool'):
        d='%_185 = icmp ne i8 %683, 0'; assert f.count(d)==1
        f=f.replace(d,'%hp = load i8, ptr %hslot, align 1\n  %_185 = icmp ne i8 %hp, 0')
    if MODE in('full','ev'):
        g='  store i8 %571, ptr %696, align 8\n'; assert f.count(g)==1
        f=f.replace(g,'  %hrx.p = getelementptr inbounds i8, ptr %_318, i64 165\n  %hrx = load i8, ptr %hrx.p, align 1\n  store i8 %hrx, ptr %696, align 8\n')
    return f
