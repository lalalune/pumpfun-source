MD="\n!99990 = !{!\"branch_weights\", i32 1, i32 2000}\n"
def addmd(t): return t+MD
EDITS=[("br i1 %112, label %bb39.i, label %bb45.i","br i1 %112, label %bb39.i, label %bb45.i, !prof !99990"),
("br i1 %96, label %bb39.i, label %bb38.i","br i1 %96, label %bb39.i, label %bb38.i, !prof !99990"),addmd]
