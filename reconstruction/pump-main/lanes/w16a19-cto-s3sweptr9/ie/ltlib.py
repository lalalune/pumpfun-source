import re
def drop_lt(block,names):
    def f(t):
        i=t.index('\n'+block+':'); j=t.index('\n\n',i+1)
        body=t[i:j]
        for n in names:
            pat=re.compile(r'\n  call void @llvm.lifetime.end.p0\(i64 \d+, ptr nonnull %'+re.escape(n)+r'\)[^\n]*')
            body,k=pat.subn('',body); assert k==1,(block,n,k)
        return t[:i]+body+t[j:]
    return f
