import re
def f(t):
    i=t.index(re.search(r'define [^\n]*admin_cto8validate',t).group(0)); j=t.index('\n}\n',i); b=t[i:j]
    x='br i1 %_20, label %bb9, label %bb10'; assert b.count(x)==1; b=b.replace(x,'br i1 %holder, label %bb9, label %bb10')
    return t[:i]+b+t[j:]
EDITS=[f]
