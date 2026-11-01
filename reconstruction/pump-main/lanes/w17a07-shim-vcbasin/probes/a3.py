# A: curve store cashback = holder ? 0 : curve.is_cashback_coin (re-read at the store); head cashback removed
EDITS=[('  %45 = and i8 %0, -3\n  %_0.sroa.0.0.off0.i.not = icmp eq i8 %45, 0\n',''),
 ('  %cashback.sroa.0.0.off0 = and i1 %_0.sroa.0.0.off0.i.not, %extract.t\n',''),
 ('  %172 = zext i1 %cashback.sroa.0.0.off0 to i8\n',''),
 ('  store i8 %172, ptr %675, align 1\n','  %cbr = load i8, ptr %675, align 1\n  %cbm = select i1 %_0.sroa.0.0.off0.i.not.i, i8 %cbr, i8 0\n  store i8 %cbm, ptr %675, align 1\n')]
