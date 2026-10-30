import runpy
EDITS=runpy.run_path('edits/ir/t1.py')['EDITS']+[("  %_123.i78 = and i1 %do_coin.sroa.0.1.off061.i, %coin_present.i\n  br i1 %_123.i78,","  %pz = zext i1 %do_coin.sroa.0.1.off061.i to i64\n  call void asm sideeffect \"\", \"{r8}\"(i64 %pz)\n  br i1 %do_coin.sroa.0.1.off061.i,")]
