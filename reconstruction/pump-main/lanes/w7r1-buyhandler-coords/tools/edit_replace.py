import os
# REP: python list of (old,new) pairs, applied once each inside buy_handler only
def edit(t):
    import re
    pairs=eval(os.environ['REP'])
    m=re.search(r'^define[^\n]*buy_v211buy_handler17h[^\n]*\n',t,re.M); s=m.start(); e=t.index('\n}\n',s)+3
    b=t[s:e]
    for o,n in pairs:
        assert b.count(o)==1,(o,b.count(o)); b=b.replace(o,n)
    return t[:s]+b+t[e:]
