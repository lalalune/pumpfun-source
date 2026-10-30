import runpy
base=runpy.run_path('ed/ir_ss_dead.py')['edit']
A='%282 = icmp eq i8 %_85.sroa.41.2157, 3'
def edit(t):
    t=base(t); assert t.count(A)==1; return t.replace(A,'%282 = icmp ugt i8 %_85.sroa.41.2157, 2')
