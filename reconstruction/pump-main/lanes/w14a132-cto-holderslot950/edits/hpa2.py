# pool arg from phi, and drop the curve re-read load entirely
EDITS=[("  %684 = load i8, ptr %683, align 1, !range !394, !noundef !2\n  %685 = icmp ne i8 %684, 0\n","  %685 = or i1 %hph, false\n")]
