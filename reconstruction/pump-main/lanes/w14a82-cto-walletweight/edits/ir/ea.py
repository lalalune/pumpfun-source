# event field from (h&-3)!=0 recomputed at the event, curve store keeps h&1
EDITS=[("  store i8 %582, ptr %710, align 8\n","  %eah = and i8 %0, -3\n  %eab = icmp ne i8 %eah, 0\n  %eaz = zext i1 %eab to i8\n  store i8 %eaz, ptr %710, align 8\n")]
