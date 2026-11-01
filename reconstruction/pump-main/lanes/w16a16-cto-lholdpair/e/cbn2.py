# same, operand order cb & new_some
EDITS=[("  %cashback.sroa.0.0.off0 = and i1 %_0.sroa.0.0.off0.i.not, %extract.t\n  %_46.sroa.0.0.copyload = load i8, ptr %new, align 1\n",
"  %_46.sroa.0.0.copyload = load i8, ptr %new, align 1\n  %newsome = icmp ne i8 %_46.sroa.0.0.copyload, 0\n  %cashback.sroa.0.0.off0 = and i1 %extract.t, %newsome\n")]
