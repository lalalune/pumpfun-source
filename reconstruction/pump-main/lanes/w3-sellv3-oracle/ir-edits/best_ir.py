import runpy,os
b=runpy.run_path('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w3-sellv3-oracle/edits/nr_swapphi58.py')['edit']
def edit(f):
    os.environ['PAIRS']='%_0.sroa.25.0,%_0.sroa.0.0'
    f=b(f)
    E=os.environ.get('EXTRA')
    if E: f=runpy.run_path(E)['edit'](f)
    return f
