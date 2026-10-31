# generic: Z0 (zero edge const), and WTS="name:a,b;name:a,b" weights on named branch conds
import os,runpy,re
D=os.path.dirname(os.path.abspath(__file__))
CONDS={'nat':'%323','rent':'%trunc.not.i123','amt':'%_124.not.not.i','ens':'%559','tn':'%562'}
def f(t):
    w=os.environ.get('WTS','')
    n=0
    for it in [x for x in w.split(';') if x]:
        k,v=it.split(':'); c=CONDS[k]
        m=re.findall(r'\n  br i1 '+re.escape(c)+r', label %[\w.]+, label %[\w.]+\n',t); assert len(m)==1,(k,len(m))
        y=m[0]; n+=1; t=t.replace(y,y[:-1]+', !prof !9999%d\n'%n); t+='\n!9999%d = !{!"branch_weights", i32 %s, i32 %s}\n'%(n,*v.split(','))
    return t
EDITS=(runpy.run_path(D+'/z0.py')['EDITS'] if os.environ.get('Z0','0')=='1' else [])+[f]
