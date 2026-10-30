EDITS=[
("""bb50.i:                                           ; preds = %bb44.i119, %bb38.i118, %bb109.i, %bb34.i
  %_406.sroa.0.0 = phi i64 [ %_406.sroa.0.2, %bb34.i ], [ 2, %bb109.i ], [ 2, %bb38.i118 ], [ 2, %bb44.i119 ]
  %_406.sroa.18.0 = phi i64 [ %_406.sroa.18.2, %bb34.i ], [ %_280.i, %bb109.i ], [ 0, %bb38.i118 ], [ 0, %bb44.i119 ]""",
"""bb50.i:                                           ; preds = %bb44.i119, %bb38.i118, %bb109.i
  %_406.sroa.0.0 = phi i64 [ 2, %bb109.i ], [ 2, %bb38.i118 ], [ 2, %bb44.i119 ]
  %_406.sroa.18.0 = phi i64 [ %_280.i, %bb109.i ], [ 0, %bb38.i118 ], [ 0, %bb44.i119 ]"""),
("""  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %rent.i), !noalias !8627
  br label %bb50.i""","""  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %rent.i), !noalias !8627
  br label %_ZN14pump_recovered9admin_cto7execute5sweep17h9943ff4781c7e018E.exit"""),
("""  %_406.sroa.0.4 = phi i64 [ %_406.sroa.0.0, %bb50.i ], [ %_406.sroa.0.3, %bb59.i105 ]
  %_406.sroa.18.4 = phi i64 [ %_406.sroa.18.0, %bb50.i ], [ %_406.sroa.18.3, %bb59.i105 ]""",
"""  %_406.sroa.0.4 = phi i64 [ %_406.sroa.0.0, %bb50.i ], [ %_406.sroa.0.3, %bb59.i105 ], [ %_406.sroa.0.2, %bb34.i ]
  %_406.sroa.18.4 = phi i64 [ %_406.sroa.18.0, %bb50.i ], [ %_406.sroa.18.3, %bb59.i105 ], [ %_406.sroa.18.2, %bb34.i ]"""),
]
