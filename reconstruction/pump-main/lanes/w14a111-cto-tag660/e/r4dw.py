import os,runpy
g=runpy.run_path('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a111-cto-tag660/e/r4d.py')
P=os.environ.get('P','1,100')
def w(t):
    x='  br i1 %509, label %bb25.i, label %bb16.i120\n'
    assert t.count(x)==1
    t=t.replace(x,x[:-1]+', !prof !99998\n'); return t+'\n!99998 = !{!"branch_weights", i32 %s, i32 %s}\n'%tuple(P.split(','))
EDITS=g['EDITS']+[w]
