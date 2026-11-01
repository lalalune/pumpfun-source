# A: outer cashback from the closure's masked holder (%46) at the join; head `and -3` removed
EDITS=[('  %45 = and i8 %0, -3\n  %_0.sroa.0.0.off0.i.not = icmp eq i8 %45, 0\n',''),
 ('  %cashback.sroa.0.0.off0 = and i1 %_0.sroa.0.0.off0.i.not, %extract.t\n',''),
 ('  %172 = zext i1 %cashback.sroa.0.0.off0 to i8\n','  %cbx = and i1 %_0.sroa.0.0.off0.i.not.i, %extract.t\n  %172 = zext i1 %cbx to i8\n')]
