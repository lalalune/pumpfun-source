EDITS=[("  %_11.i262 = alloca [0 x i8], align 1\n","  %_11.i262 = alloca [0 x i8], align 1\n  %tagslot = alloca i8, align 1\n"),
("  %_502.sroa.0.0.off0 = phi i1 [ false, %bb17 ], [ false, %bb18 ], [ false, %bb19 ], [ true, %bb15 ]\n","  %_502.sroa.0.0.off0 = phi i1 [ false, %bb17 ], [ false, %bb18 ], [ false, %bb19 ], [ true, %bb15 ]\n  store i8 %_501.sroa.0.0, ptr %tagslot, align 1\n"),
("  %704 = zext i1 %564 to i8\n","  %tagl = load i8, ptr %tagslot, align 1\n  %tagc = icmp ne i8 %tagl, 2\n  %704 = zext i1 %tagc to i8\n")]
