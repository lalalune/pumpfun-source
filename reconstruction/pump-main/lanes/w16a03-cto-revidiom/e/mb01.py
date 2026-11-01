import runpy,os
E=runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)),'vb01.py'))['EDITS']
EDITS=E[1:]
