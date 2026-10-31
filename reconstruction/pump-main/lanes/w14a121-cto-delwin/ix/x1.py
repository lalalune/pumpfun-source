P="  %_554.sroa.0.0.off0 = phi i1 [ false, %bb20 ], [ false, %bb21 ], [ false, %bb22 ], [ true, %bb18 ]\n"
EDITS=[("  %578 = icmp ne i8 %_553.sroa.0.0, 2\n  br i1 %578,","  br i1 %r578,"),("  %718 = zext i1 %578 to i8","  %718 = zext i1 %r578 to i8"),(P,P+"  %r578 = icmp ne i8 %_553.sroa.0.0, 2\n")]
