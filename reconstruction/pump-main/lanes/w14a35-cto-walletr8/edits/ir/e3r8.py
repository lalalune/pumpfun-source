import runpy
EDITS=runpy.run_path('edits/ir/e3.py')['EDITS']+[('  store i64 %_95.sroa.0.0, ptr %704, align 8','  call void asm sideeffect "", "{r8}"(i64 %_95.sroa.0.0)\n  store i64 %_95.sroa.0.0, ptr %704, align 8')]
