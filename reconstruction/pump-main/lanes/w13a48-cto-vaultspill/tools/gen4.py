import runpy
hk=runpy.run_path('hk1.py')['EDITS']
for b in ['bumparg','bumptop','bumpafterdest','nativeafterdest','tuple_dest_all','arg_cmp']:
    e=runpy.run_path(b+'.py')['EDITS']
    open('hk1_'+b+'.py','w').write('EDITS='+repr(hk+e)+'\n')
