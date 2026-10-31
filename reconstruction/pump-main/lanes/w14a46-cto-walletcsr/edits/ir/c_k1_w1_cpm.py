import runpy
EDITS=[]
EDITS+=runpy.run_path('e/ir/k1.py')['EDITS']
EDITS+=runpy.run_path('e/ir/w1.py')['EDITS']
EDITS+=runpy.run_path('e/ir/cpm.py')['EDITS']
