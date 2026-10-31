import os,runpy
D=os.path.dirname(os.path.abspath(__file__))
W=os.environ.get('W','0')
def f(t):
    if W!='0':
        y='  br i1 %_124.not.not.i, label %bb30.i, label %bb48.i118\n'
        assert t.count(y)==1; t=t.replace(y,y[:-1]+', !prof !99999\n'); t+='\n!99999 = !{!"branch_weights", i32 %s, i32 %s}\n'%tuple(W.split(','))
    return t
EDITS=(runpy.run_path(D+'/z0.py')['EDITS'] if os.environ.get('Z0','1')=='1' else [])+[f]
