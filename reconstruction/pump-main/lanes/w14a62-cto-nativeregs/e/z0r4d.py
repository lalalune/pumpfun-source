import runpy,os
D=os.path.dirname(os.path.abspath(__file__))
EDITS=(runpy.run_path(D+'/z0.py')['EDITS'] if os.environ.get('Z0','1')=='1' else [])+runpy.run_path(D+'/r4d.py')['EDITS']
