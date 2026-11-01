# split IR bb11 before the max_fee load (fee_cfg, cashback, creator memcpy in bb11; rest in bb11s)
EDITS=[("  %31 = getelementptr inbounds i8, ptr %_282, i64 1072\n","  br label %bb11s\n\nbb11s:\n  %31 = getelementptr inbounds i8, ptr %_282, i64 1072\n")]
