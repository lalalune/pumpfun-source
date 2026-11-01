# cashback select as an explicit branch diamond (cashback byte test first)
EDITS=[("  %cashback.sroa.0.0.off0 = and i1 %_0.sroa.0.0.off0.i.not, %extract.t\n",
"  br i1 %extract.t, label %cbA, label %cbJ\n\ncbA:\n  br label %cbJ\n\ncbJ:\n  %cashback.sroa.0.0.off0 = phi i1 [ %_0.sroa.0.0.off0.i.not, %cbA ], [ false, %bb11 ]\n")]
