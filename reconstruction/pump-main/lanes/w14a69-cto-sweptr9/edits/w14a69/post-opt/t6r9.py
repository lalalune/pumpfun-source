import runpy
EDITS=runpy.run_path('pe/t6.py')['EDITS']+[('  store i64 %_95.sroa.0.0, ptr %715, align 8','  call void asm sideeffect "", "{r9}"(i64 %_95.sroa.0.0)\n  store i64 %_95.sroa.0.0, ptr %715, align 8')]
