# (a2) Ok uses reload at the event store; shared loads only feed the Err phi
EDITS=[("""  store i64 %_196.0.i, ptr %249, align 8, !noalias !8603""","""  %q196.0 = load i64, ptr %246, align 8
  store i64 %q196.0, ptr %249, align 8, !noalias !8603"""),("""  store ptr %_196.1.i, ptr %250, align 8, !noalias !8603""","""  %q196.1 = load ptr, ptr %247, align 8
  store ptr %q196.1, ptr %250, align 8, !noalias !8603""")]
