# curve store from (h&-3)!=0, event keeps h&1 (recomputed at the event)
EDITS=[("  %582 = and i8 %0, 1\n","  %ebh = and i8 %0, -3\n  %ebb = icmp ne i8 %ebh, 0\n  %582 = zext i1 %ebb to i8\n"),("  store i8 %582, ptr %710, align 8\n","  %ebe = and i8 %0, 1\n  store i8 %ebe, ptr %710, align 8\n")]
