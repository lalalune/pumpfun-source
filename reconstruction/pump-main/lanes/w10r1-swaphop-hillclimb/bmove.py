"""Edit helper: move(text, block, after) moves IR block `block` of swap_hop to just after block `after`."""
import re
def _split(t):
    s = t.index('define '); s = t.index('\n', [m.start() for m in re.finditer(r'^define .*multi_hop_curve8swap_hop17h', t, re.M)][0]) + 1
    e = t.index('\n}\n', s) + 1
    body = t[s:e]
    body = re.sub(r'%(\d+)\b', r'%v\1', body)
    body = re.sub(r'(?m)^(\d+):', r'v\1:', body)
    parts = re.split(r'(?m)^(?=[\w.$"-]+:)', body)
    return t[:s], parts, t[e:]
def lab(p): return p.split(':', 1)[0].strip('"')
def move(t, block, after):
    pre, parts, post = _split(t)
    i = next(k for k, p in enumerate(parts) if lab(p) == block)
    b = parts.pop(i)
    j = next(k for k, p in enumerate(parts) if lab(p) == after)
    parts.insert(j + 1, b)
    return pre + ''.join(parts) + post
