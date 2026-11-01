# oracle: gate polarity as the original (br skip -> join, else sweep): invert the !skip phi and swap the branch targets
EDITS=[
 ("  %_552.sroa.0.0.off0 = phi i1 [ false, %bb20 ], [ false, %bb21 ], [ false, %bb22 ], [ true, %bb18 ]\n","  %_552.sroa.0.0.off0 = phi i1 [ true, %bb20 ], [ true, %bb21 ], [ true, %bb22 ], [ false, %bb18 ]\n"),
 ("  br i1 %_552.sroa.0.0.off0, label %bb83, label %bb88\n","  br i1 %_552.sroa.0.0.off0, label %bb88, label %bb83\n"),
]
