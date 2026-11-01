# (a'') holder test reads the holder arg through a stack copy written after the st stores (deeper dependency for the !holder select)
EDITS=[("  %i45 = and i8 %arg, -3\n","  %hst = getelementptr inbounds i8, ptr %st, i64 47\n  store i8 %arg, ptr %hst, align 1\n  %hrl = load volatile i8, ptr %hst, align 1\n  %i45 = and i8 %hrl, -3\n")]
