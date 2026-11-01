# split IR bb11 right after the cashback and (select stays with the loads, new tag + sk1 copy move on)
EDITS=[("  %cashback.sroa.0.0.off0 = and i1 %_0.sroa.0.0.off0.i.not, %extract.t\n","  %cashback.sroa.0.0.off0 = and i1 %_0.sroa.0.0.off0.i.not, %extract.t\n  br label %bb11s\n\nbb11s:\n")]
