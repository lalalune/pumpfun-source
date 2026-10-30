import runpy
EDITS=[]
EDITS+=runpy.run_path('edits/v1.py')['EDITS']
EDITS+=runpy.run_path('edits/pf.py')['EDITS']
