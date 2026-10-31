EDITS=[
 ('bb22:                                             ; preds = %bb76\n  br i1','bb22:                                             ; preds = %bb76\n  %hA = and i8 %arg, 1\n  br i1'),
 ('  %_554.sroa.0.0.off0 = phi i1 [ false, %bb21 ], [ false, %bb22 ], [ false, %bb23 ], [ true, %bb19 ]\n','  %_554.sroa.0.0.off0 = phi i1 [ false, %bb21 ], [ false, %bb22 ], [ false, %bb23 ], [ true, %bb19 ]\n  %hflag = phi i8 [ 0, %bb21 ], [ %hA, %bb22 ], [ %hA, %bb23 ], [ 1, %bb19 ]\n'),
 ('  %i581 = and i8 %arg, 1\n','  %i581 = or i8 %hflag, 0\n'),
]
