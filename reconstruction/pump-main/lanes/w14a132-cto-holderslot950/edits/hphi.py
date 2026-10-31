# per-arm holder phi of constants at validate's exits (bb54.i merge, bb75 exit)
EDITS=[
("bb54.i:                                           ; preds = %bb95.i, %bb52.i\n",
 "bb54.i:                                           ; preds = %bb95.i, %bb52.i\n  %hph54 = phi i1 [ false, %bb52.i ], [ true, %bb95.i ]\n"),
("bb75:                                             ; preds = %bb65.i, %bb44.i, %bb45.i\n",
 "bb75:                                             ; preds = %bb65.i, %bb44.i, %bb45.i\n  %hph = phi i1 [ false, %bb45.i ], [ %hph54, %bb65.i ], [ true, %bb44.i ]\n"),
]
