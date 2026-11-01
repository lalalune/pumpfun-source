# cashback select as an explicit branch diamond (holder test first)
EDITS=[("  %cashback.sroa.0.0.off0 = and i1 %_0.sroa.0.0.off0.i.not, %extract.t\n",
"  br i1 %_0.sroa.0.0.off0.i.not, label %cbA, label %cbJ\n\ncbA:\n  br label %cbJ\n\ncbJ:\n  %cashback.sroa.0.0.off0 = phi i1 [ %extract.t, %cbA ], [ false, %bb11 ]\n")]
