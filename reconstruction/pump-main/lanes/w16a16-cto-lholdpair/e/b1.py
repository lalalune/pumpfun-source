# split IR bb11 right before the holder/cashback select computation
EDITS=[("  store i8 %27, ptr %45, align 1\n  %46 = and i8 %0, -3\n","  store i8 %27, ptr %45, align 1\n  br label %bb11s\n\nbb11s:\n  %46 = and i8 %0, -3\n")]
