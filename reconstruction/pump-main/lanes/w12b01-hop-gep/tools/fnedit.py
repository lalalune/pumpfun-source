import re
FN='multi_hop_curve8swap_hop17h'
def fn_span(t):
    m=re.search(r'\ndefine[^\n]*'+FN+r'[^\n]*\{\n',t); s=m.end(); e=t.find('\n}\n',s)
    return s,e
def sub_fn(t, old, new, count=1):
    s,e=fn_span(t); body=t[s:e]
    assert body.count(old)==count, (old, body.count(old))
    return t[:s]+body.replace(old,new)+t[e:]
