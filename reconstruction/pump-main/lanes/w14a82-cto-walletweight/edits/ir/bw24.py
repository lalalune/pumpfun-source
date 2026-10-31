# branch weight 4:1 on the wallet ATA create_idempotent Ok test (bb24.i)
EDITS=[("  %238 = icmp eq i64 %237, 2\n  br i1 %238, label %bb26.i, label %bb79.i77\n","  %238 = icmp eq i64 %237, 2\n  br i1 %238, label %bb26.i, label %bb79.i77, !prof !99990\n"),
 (lambda t: t+"\n!99990 = !{!\"branch_weights\", i32 4, i32 1}\n")]
