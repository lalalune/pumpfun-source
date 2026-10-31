import runpy
EDITS=runpy.run_path('pe/e1.py')['EDITS']+[('  store i64 %_89.sroa.0.0, ptr %705, align 8','  call void asm sideeffect "", "{r9}"(i64 %_89.sroa.0.0)\n  store i64 %_89.sroa.0.0, ptr %705, align 8')]
