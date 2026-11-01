# (d) validate's holder branches test the materialized !holder byte from bb11 (no holder-arg use in bb6.i)
EDITS=[("  %cashback.sroa.0.0.off0 = and i1 %_0.sroa.0.0.off0.i.not, %extract.t\n",
"  %cashback.sroa.0.0.off0 = and i1 %_0.sroa.0.0.off0.i.not, %extract.t\n  %hnz = zext i1 %_0.sroa.0.0.off0.i.not to i8\n"),
("bb14.i:                                           ; preds = %bb6.i\n  br i1 %_0.sroa.0.0.off0.i.not, label %bb23.i, label %bb16.i\n",
"bb14.i:                                           ; preds = %bb6.i\n  %hn1 = icmp ne i8 %hnz, 0\n  br i1 %hn1, label %bb23.i, label %bb16.i\n"),
("bb7.i:                                            ; preds = %bb6.i\n  br i1 %_0.sroa.0.0.off0.i.not, label %bb10.i, label %bb22.i\n",
"bb7.i:                                            ; preds = %bb6.i\n  %hn2 = icmp ne i8 %hnz, 0\n  br i1 %hn2, label %bb10.i, label %bb22.i\n")]
