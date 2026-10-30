import os,re
# PROF: list of (branch_text, "w1, w2")
def edit(t):
    pairs=eval(os.environ['PROF'])
    m=re.search(r'^define[^\n]*buy_v211buy_handler17h[^\n]*\n',t,re.M); s=m.start(); e=t.index('\n}\n',s)+3
    b=t[s:e]; extra=''
    for i,(br,w) in enumerate(pairs):
        assert b.count(br)==1,(br,b.count(br))
        b=b.replace(br,br+', !prof !%d'%(9999990+i)); extra+='!%d = !{!"branch_weights", %s}\n'%(9999990+i,w)
    return t[:s]+b+t[e:]+extra
