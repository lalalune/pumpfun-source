# e2 (p289h emulated as xor on %holder: V-time threading) but 307/312 to_string call sites alwaysinline (no outlining)
import re,runpy,os
E2=runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)),'e2.py'))['EDITS'][0]
def f(t):
    t=E2(t)
    i=t.index(re.search(r'define [^\n]*admin_cto8validate',t).group(0)); j=t.index('\n}\n',i)
    L=t[i:j].split('\n'); code=None; n=0
    for k,l in enumerate(L):
        m=re.search(r'for\$u20\$u32\$GT\$4from\S*\(i32 noundef (\d+)\)',l)
        if m: code=int(m.group(1))
        if '9to_string' in l and 'call' in l and code in (30,19):
            L[k]=re.sub(r' #\d+$',' #9003',l); assert L[k]!=l; n+=1
    assert n==2,n
    return t[:i]+'\n'.join(L)+t[j:]+'\nattributes #9003 = { alwaysinline }\n'
EDITS=[f]
