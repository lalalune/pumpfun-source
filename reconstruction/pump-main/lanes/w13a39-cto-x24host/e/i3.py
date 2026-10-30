import runpy
EDITS=runpy.run_path('e/i2.py')['EDITS']+[("  %holder_key = alloca [32 x i8], align 1\n","  %x24 = alloca [24 x i8], align 8\n  %holder_key = alloca [32 x i8], align 1\n")]
