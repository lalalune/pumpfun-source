# (a) Err edge of collect reloads the payload words itself
EDITS=[("""bb81.i:                                           ; preds = %bb27.i80
  call void @llvm.lifetime.end.p0(i64 48, ptr nonnull %_58.i), !noalias !8603""","""bb81.i:                                           ; preds = %bb27.i80
  %r196.0 = load i64, ptr %246, align 8
  %r196.1 = load ptr, ptr %247, align 8
  call void @llvm.lifetime.end.p0(i64 48, ptr nonnull %_58.i), !noalias !8603"""),
("phi ptr [ %_196.1.i, %bb81.i ]","phi ptr [ %r196.1, %bb81.i ]"),("phi i64 [ %_196.0.i, %bb81.i ]","phi i64 [ %r196.0, %bb81.i ]")]
