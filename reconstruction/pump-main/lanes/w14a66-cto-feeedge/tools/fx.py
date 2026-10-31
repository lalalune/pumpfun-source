# helper: apply (old,new) edits inside execute's body only
FN='@_ZN14pump_recovered9admin_cto7execute17h'
def inexec(pairs):
    def f(t):
        k=t.index('define hidden { i64, ptr } '+FN); e=t.index('\n}\n',k)
        b=t[k:e]
        for x,y in pairs:
            c=b.count(x); assert c==1,(c,x[:120]); b=b.replace(x,y)
        return t[:k]+b+t[e:]
    return f
