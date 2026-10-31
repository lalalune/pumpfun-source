import os,runpy
q1=runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)),'q1.py'))['f']
W=os.environ.get('W','3,1')
def g(t):
    t=q1(t)
    x='  br i1 %_123.not.not.i, label %bb30.i, label %_ZN14pump_recovered9admin_cto7execute5sweep17h9943ff4781c7e018E.exit\n'
    assert t.count(x)==1
    t=t.replace(x,x[:-1]+', !prof !99999\n')
    t+='\n!99999 = !{!"branch_weights", i32 %s, i32 %s}\n'%tuple(W.split(','))
    return t
EDITS=[g]
