# (b) Ok path stores collected / quote word into the event alloca right at the definition (bb82.i)
EDITS=[("""  call void @llvm.lifetime.start.p0(i64 80, ptr nonnull %e.i), !noalias !8603
  call void @llvm.lifetime.start.p0(i64 48, ptr nonnull %_75.i64), !noalias !8603""","""  call void @llvm.lifetime.start.p0(i64 48, ptr nonnull %_75.i64), !noalias !8603"""),
("""bb82.i:                                           ; preds = %bb27.i80
""","""bb82.i:                                           ; preds = %bb27.i80
  call void @llvm.lifetime.start.p0(i64 80, ptr nonnull %e.i), !noalias !8603
  %b249 = getelementptr inbounds i8, ptr %e.i, i64 72
  store i64 %_196.0.i, ptr %b249, align 8
  %b250 = getelementptr inbounds i8, ptr %e.i, i64 32
  store ptr %_196.1.i, ptr %b250, align 8
"""),("""  store i64 %_196.0.i, ptr %249, align 8, !noalias !8603
""",""),("""  store ptr %_196.1.i, ptr %250, align 8, !noalias !8603
""","")]
