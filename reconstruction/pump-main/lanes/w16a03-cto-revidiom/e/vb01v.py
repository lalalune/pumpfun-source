import runpy,os
E=runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)),'vb01.py'))['EDITS']
EDITS=[(a,b) if a!="if t==*sharing||t==*holder_key{" else (a,"if t==holder_key||t==*sharing{") for a,b in E]
