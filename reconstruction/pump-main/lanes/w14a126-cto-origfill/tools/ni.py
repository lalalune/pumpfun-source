import re,os
CODES=[int(x) for x in os.environ.get('NI','30,19').split(',') if x]
def f(t):
    i=t.index(re.search(r'define [^\n]*admin_cto8validate',t).group(0)); j=t.index('\n}\n',i)
    L=t[i:j].split('\n'); code=None; n=0
    for k,l in enumerate(L):
        m=re.search(r'for\$u20\$u32\$GT\$4from\S*\(i32 noundef (\d+)\)',l)
        if m: code=int(m.group(1))
        if '9to_string' in l and 'call' in l and code in CODES:
            L[k]=re.sub(r' #\d+$',' #9001',l); assert L[k]!=l; n+=1
    assert n==len(CODES),n
    return t[:i]+'\n'.join(L)+t[j:]+'\nattributes #9001 = { noinline }\n'
EDITS=[f]
