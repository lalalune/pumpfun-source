# carry the closure's masked holder through a NEW volatile alloca: store at def, reload at the curve store
EDITS=[('start:\n','start:\n  %hslot = alloca i8, align 1\n'),
 ('  %46 = and i8 %0, 1\n','  %46 = and i8 %0, 1\n  store volatile i8 %46, ptr %hslot, align 1\n'),
 ('  store i8 %46, ptr %674, align 1\n','  %hv = load volatile i8, ptr %hslot, align 1\n  store i8 %hv, ptr %674, align 1\n')]
