import re
def name_fn(t):
    s = t.index('swap_hop17h'); s = t.rindex('\ndefine', 0, s); e = t.index('\n}\n', s)
    body = t[s:e]
    body = re.sub(r'%(\d+)\b', r'%v\1', body)
    return t[:s] + body + t[e:]
