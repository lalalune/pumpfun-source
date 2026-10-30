def edit(t):
    old = "bb147:                                            ; preds = %\"_ZN4core3ptr52drop_in_place$LT$solana_instruction..Instruction$GT$17h3ecb6a9b9e1b11acE.exit\"\n  store i8 1, ptr %5, align 1\n"
    assert t.count(old) == 1
    new = old.replace("  store i8 1, ptr %5, align 1\n", "  %hv2 = load ptr, ptr %1, align 8\n  %hv2c = getelementptr inbounds i8, ptr %hv2, i64 161\n  store i8 1, ptr %hv2c, align 1\n")
    t = t.replace(old, new)
    t = t.replace("%_1056 = load ptr, ptr %h.val, align 8", "%_1056 = load ptr, ptr %hv2, align 8")
    return t
