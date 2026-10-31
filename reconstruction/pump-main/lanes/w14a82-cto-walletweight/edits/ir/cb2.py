# recompute cashback at its store from the entry is_cashback_coin bool and the holder arg (h&1)
EDITS=[("  store i8 %169, ptr %581, align 1\n","  %cbh = and i8 %0, 1\n  %cbn = icmp eq i8 %cbh, 0\n  %cba = and i1 %cbn, %extract.t\n  %cbz = zext i1 %cba to i8\n  store i8 %cbz, ptr %581, align 1\n")]
