EDITS=[("  %582 = and i8 %0, 1\n","  %hh = and i8 %0, -3\n  %hb = icmp ne i8 %hh, 0\n  %582 = zext i1 %hb to i8\n")]
