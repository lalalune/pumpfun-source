J69="bb69:                                             ; preds = %bb58.i, %bb44.i, %bb45.i\n"
J54="bb54.i:                                           ; preds = %bb93.i, %bb52.i\n"
CBDEF="  %43 = xor i1 %_0.sroa.0.0.off0.i45, true\n  %cashback.sroa.0.0.off0 = and i1 %_40.not, %43\n"
CBUSE="%167 = zext i1 %cashback.sroa.0.0.off0 to i8"
HUSE1="br i1 %_0.sroa.0.0.off0.i45, label %bb23, label %bb18"
HUSE2="%571 = zext i1 %_0.sroa.0.0.off0.i45 to i8"
B45="  %switch12.i = icmp eq i64 %0, 0\n  br i1 %switch12.i, label %bb69, label %bb47.i\n"
EDITS=[(J54,J54+"  %hA = phi i1 [ false, %bb52.i ], [ true, %bb93.i ]\n"),(J69,J69+"  %hJ = phi i1 [ false, %bb45.i ], [ %hA, %bb58.i ], [ true, %bb44.i ]\n"),(HUSE1,"br i1 %hJ, label %bb23, label %bb18"),(HUSE2,"%571 = zext i1 %hJ to i8")]
