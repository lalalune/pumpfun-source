import runpy,os
d=os.path.dirname(__file__)
EDITS=runpy.run_path(d+'/cbR.py')['EDITS']+runpy.run_path(d+'/hR.py')['EDITS']
