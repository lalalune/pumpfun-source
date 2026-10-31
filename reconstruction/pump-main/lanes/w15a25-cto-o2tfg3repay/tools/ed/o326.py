# IR-forced O (307/312 to_string call sites noinline) + the 326 call site alwaysinline (inlined at validate's visit, as T289n)
import re
def f(t):
    i=t.index(re.search(r'define [^\n]*admin_cto8validate',t).group(0)); j=t.index('\n}\n',i)
    L=t[i:j].split('\n'); code=None; n=0
    for k,l in enumerate(L):
        m=re.search(r'for\$u20\$u32\$GT\$4from\S*\(i32 noundef (\d+)\)',l)
        if m: code=int(m.group(1))
        if '9to_string' in l and 'call' in l and code in (30,19,91):
            L[k]=re.sub(r' #\d+$',' #9001' if code!=91 else ' #9003',l); assert L[k]!=l; n+=1
    assert n==3,n
    return t[:i]+'\n'.join(L)+t[j:]+'\nattributes #9001 = { noinline }\nattributes #9003 = { alwaysinline }\n'
EDITS=[f]
