P="  %_553.sroa.0.0 = phi i8 [ %_45.sroa.0.0.copyload, %bb20 ], [ 2, %bb21 ], [ 2, %bb22 ], [ 0, %bb18 ]\n"
EDITS=[("  %718 = zext i1 %578 to i8","  %718 = zext i1 %rs to i8"),(P,P+"  %rs = phi i1 [ true, %bb20 ], [ false, %bb21 ], [ false, %bb22 ], [ true, %bb18 ]\n")]
