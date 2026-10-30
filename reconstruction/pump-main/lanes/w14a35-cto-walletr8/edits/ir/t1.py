# tag (sharing_update discriminant) through its own i8 alloca: stored at def, reloaded at both uses (bound only)
EDITS=[("start:\n  %_11.i268 = alloca [0 x i8], align 1\n","start:\n  %tagsl = alloca i8, align 1\n  %_11.i268 = alloca [0 x i8], align 1\n"),
("  %_540.sroa.0.0.off0 = phi i1 [ false, %bb21 ], [ false, %bb22 ], [ false, %bb23 ], [ true, %bb19 ]\n","  %_540.sroa.0.0.off0 = phi i1 [ false, %bb21 ], [ false, %bb22 ], [ false, %bb23 ], [ true, %bb19 ]\n  store volatile i8 %_539.sroa.0.0, ptr %tagsl, align 1\n"),
("  %565 = icmp ne i8 %_539.sroa.0.0, 2","  %tg1 = load volatile i8, ptr %tagsl, align 1\n  %565 = icmp ne i8 %tg1, 2"),
("  store i8 %_539.sroa.0.0, ptr %val6, align 1","  %tg2 = load volatile i8, ptr %tagsl, align 1\n  store i8 %tg2, ptr %val6, align 1")]
