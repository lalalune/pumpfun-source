# carry the outer holder i8 (%45 = and %0,-3) through a NEW volatile alloca to the shared-arm branch
EDITS=[('start:\n','start:\n  %islot = alloca i8, align 1\n'),
 ('  %45 = and i8 %0, -3\n','  %45 = and i8 %0, -3\n  store volatile i8 %45, ptr %islot, align 1\n'),
 ('  br i1 %_0.sroa.0.0.off0.i.not, label %bb20, label %bb25\n','  %iv = load volatile i8, ptr %islot, align 1\n  %ivc = icmp eq i8 %iv, 0\n  br i1 %ivc, label %bb20, label %bb25\n')]
