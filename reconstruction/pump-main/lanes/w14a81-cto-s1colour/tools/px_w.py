import os,re
W=[tuple(int(v) for v in x.split(':')) for x in os.environ.get('PXW','').split(',') if x]
def f(t):
    s=t.index('define hidden { i64, ptr } @_ZN14pump_recovered9admin_cto7execute'); e=t.index('\n}\n',s)
    ms=list(re.finditer(r'\n  br i1 (%[\w.]+), label %([\w.$"]+), label %([\w.$"]+)\n',t[s:e]))
    reps=sorted(((s+ms[i].end()-1,i,a,b) for i,a,b in W),reverse=True); md=[]
    for n,(a1,i,a,b) in enumerate(reps):
        t=t[:a1]+', !prof !9999%d'%n+t[a1:]; md.append('!9999%d = !{!"branch_weights", i32 %d, i32 %d}'%(n,a,b))
    return t+'\n'+'\n'.join(md)+'\n'
EDITS=[f]
