# per-arm cashback phi (= !holder && st.cashback) at validate exits, consumed at the curve +0xa3 store
EDITS=[
("bb54.i:                                           ; preds = %bb95.i, %bb52.i\n",
 "bb54.i:                                           ; preds = %bb95.i, %bb52.i\n  %cb54 = phi i1 [ %extract.t, %bb52.i ], [ false, %bb95.i ]\n"),
("bb75:                                             ; preds = %bb65.i, %bb44.i, %bb45.i\n",
 "bb75:                                             ; preds = %bb65.i, %bb44.i, %bb45.i\n  %cbph = phi i1 [ %extract.t, %bb45.i ], [ %cb54, %bb65.i ], [ false, %bb44.i ]\n"),
("  %170 = zext i1 %cashback.sroa.0.0.off0 to i8\n","  %170 = zext i1 %cbph to i8\n"),
]
