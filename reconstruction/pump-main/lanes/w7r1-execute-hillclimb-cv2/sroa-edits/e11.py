import runpy
def edit(f):
    f=runpy.run_path('sx/e9.py')['edit'](f); return runpy.run_path('sx/e10.py')['edit'](f)
