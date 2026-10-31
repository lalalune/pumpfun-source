# recompute the holder bool at its post-sweep use (bonding_curve.is_holder_reward store) from the holder arg
EDITS=[("  %582 = zext i1 %_0.sroa.0.0.off0.i to i8\n","  %hrh = and i8 %holder, -3\n  %hrb = icmp ne i8 %hrh, 0\n  %582 = zext i1 %hrb to i8\n")]
