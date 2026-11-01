# volatile slot holds the RAW hopt; shared-arm branch recomputes and -3 from a reload
EDITS=[('start:\n','start:\n  %rslot = alloca i8, align 1\n  store volatile i8 %0, ptr %rslot, align 1\n'),
 ('  br i1 %_0.sroa.0.0.off0.i.not, label %bb20, label %bb25\n','  %rv = load volatile i8, ptr %rslot, align 1\n  %rv3 = and i8 %rv, -3\n  %rvc = icmp eq i8 %rv3, 0\n  br i1 %rvc, label %bb20, label %bb25\n')]
