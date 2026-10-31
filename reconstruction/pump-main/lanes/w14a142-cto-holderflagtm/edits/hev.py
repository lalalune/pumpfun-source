# event is_holder_reward from the holder arg (keeps %0 live past the curve store)
EDITS=[("  %708 = load i8, ptr %707, align 1, !range !394, !noundef !2\n","  %708 = and i8 %0, 1\n")]
