# skip-polarity gate: phi holds skip (not !skip), branch on skip with swapped targets
EDITS=[("  %_540.sroa.0.0.off0 = phi i1 [ false, %bb21 ], [ false, %bb22 ], [ false, %bb23 ], [ true, %bb19 ]\n","  %_540.sroa.0.0.off0 = phi i1 [ true, %bb21 ], [ true, %bb22 ], [ true, %bb23 ], [ false, %bb19 ]\n"),
("  br i1 %_540.sroa.0.0.off0, label %bb84, label %bb89\n","  br i1 %_540.sroa.0.0.off0, label %bb89, label %bb84\n")]
