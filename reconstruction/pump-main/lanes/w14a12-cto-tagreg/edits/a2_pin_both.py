EDITS=[("  %704 = zext i1 %564 to i8\n","  %tz = zext i8 %_501.sroa.0.0 to i64\n  call void asm sideeffect \"\", \"{r6}\"(i64 %tz)\n  %704 = zext i1 %564 to i8\n"),
("  %564 = icmp ne i8 %_501.sroa.0.0, 2\n","  %tz0 = zext i8 %_501.sroa.0.0 to i64\n  call void asm sideeffect \"\", \"{r6}\"(i64 %tz0)\n  %564 = icmp ne i8 %_501.sroa.0.0, 2\n")]
