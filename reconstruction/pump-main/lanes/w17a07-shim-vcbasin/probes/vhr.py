# raw hopt in a volatile slot; curve store reloads and masks it (and 1); shared arm unchanged
EDITS=[('start:\n','start:\n  %rslot = alloca i8, align 1\n  store volatile i8 %0, ptr %rslot, align 1\n'),
 ('  store i8 %46, ptr %674, align 1\n','  %rv = load volatile i8, ptr %rslot, align 1\n  %rv1 = and i8 %rv, 1\n  store i8 %rv1, ptr %674, align 1\n')]
