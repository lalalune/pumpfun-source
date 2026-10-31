# IR: the shared arm's Some(args.0) payload read straight from the `new` argument (forward execute's args=(new,) copy)
import re
def f(t):
    i=t.index(re.search(r'define [^\n]*admin_cto7execute',t).group(0)); j=t.index('\n}\n',i); b=t[i:j]
    x='call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_63, ptr align 1 %_45, i64 33, i1 false)'; assert b.count(x)==1
    b=b.replace(x,'call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_63, ptr align 1 %new, i64 33, i1 false)')
    return t[:i]+b+t[j:]
EDITS=[f]
