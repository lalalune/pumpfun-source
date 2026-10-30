EDITS=[("  %nf = load i64, ptr %663, align 8, !noundef !2\n",""),
("  store i64 %nf, ptr %702, align 8\n","  %nfx = getelementptr inbounds i8, ptr %_319, i64 112\n  %nf = load i64, ptr %nfx, align 8\n  store i64 %nf, ptr %702, align 8\n")]
