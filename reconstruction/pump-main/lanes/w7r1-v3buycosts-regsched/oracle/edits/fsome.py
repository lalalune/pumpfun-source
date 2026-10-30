import os,runpy
os.environ.update(TY='i64',POL='some',CMP='ne')
def edit(f): return runpy.run_path(os.path.dirname(__file__)+'/flaggen.py')['edit'](f)
