# oracle: cashback flag through a stack slot written at the head (emulates a spilled per-arm cashback flag)
EDITS=[
 ("  %_267 = alloca [1 x i8], align 1\n","  %_267 = alloca [1 x i8], align 1\n  %cbm = alloca [1 x i8], align 1\n"),
 ("  %cashback.sroa.0.0.off0 = and i1 %_0.sroa.0.0.off0.i.not, %extract.t\n","  %cashback.sroa.0.0.off0 = and i1 %_0.sroa.0.0.off0.i.not, %extract.t\n  %cbz = zext i1 %cashback.sroa.0.0.off0 to i8\n  store i8 %cbz, ptr %cbm, align 1\n"),
 ("  %170 = zext i1 %cashback.sroa.0.0.off0 to i8\n",""),
 ("  store i8 %170, ptr %583, align 1\n","  %cbl = load i8, ptr %cbm, align 1\n  store i8 %cbl, ptr %583, align 1\n"),
]
