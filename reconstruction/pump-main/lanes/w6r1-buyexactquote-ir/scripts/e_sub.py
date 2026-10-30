import os,re
# SUBS file: python list of (old,new) applied once each within target function
def edit(t):
    subs=eval(open(os.environ['SUBS']).read())
    s=t.index('define hidden { i64, ptr } @_ZN14pump_recovered5trade15buy_exact_quote17h'); e=t.index('\n}\n',s)
    f=t[s:e]
    for o,n in subs:
        assert f.count(o)==1,(f.count(o),o[:60]); f=f.replace(o,n)
    return t[:s]+f+t[e:]
