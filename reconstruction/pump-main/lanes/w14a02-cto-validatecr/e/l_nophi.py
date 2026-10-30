EDITS=[("  %_254.pre = load ptr, ptr %7, align 8\n",""),
("  %_273 = phi ptr [ %_254.pre, %bb3 ], [ %_249, %start ], [ %_249, %bb2 ]\n  %shared.sroa.0.0.off0 = phi i1 [ %14, %bb3 ], [ false, %start ], [ false, %bb2 ]\n",
 "  %shared.sroa.0.0.off0 = phi i1 [ %14, %bb3 ], [ false, %start ], [ false, %bb2 ]\n  %_273 = load ptr, ptr %7, align 8, !nonnull !2, !align !3, !noundef !2\n")]
