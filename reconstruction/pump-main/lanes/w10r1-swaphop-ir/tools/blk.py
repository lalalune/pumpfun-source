"""helpers: split swap_hop body into blocks; move blocks."""
import re
FN = re.compile(r'^define .*multi_hop_curve8swap_hop17h.*$', re.M)
def split(t):
    m = FN.search(t); s = m.start(); e = t.index('\n}\n', s) + 3
    body = t[s:e]; lines = body.split('\n')
    hdr = []; blocks = []; cur = None
    for ln in lines[:-2]:
        mm = re.match(r'^([\w.\-]+):', ln)
        if mm:
            cur = [mm.group(1), [ln]]; blocks.append(cur); continue
        if cur is None: hdr.append(ln)
        else: cur[1].append(ln)
    return t[:s], hdr, blocks, t[e:]
def join(pre, hdr, blocks, post):
    return pre + '\n'.join(hdr + [l for b in blocks for l in b[1]]) + '\n}\n' + post
def move(t, names, after):
    pre, hdr, blocks, post = split(t)
    mv = [b for n in names for b in blocks if b[0] == n]
    rest = [b for b in blocks if b[0] not in names]
    i = next(k for k, b in enumerate(rest) if b[0] == after)
    rest[i + 1:i + 1] = mv
    return join(pre, hdr, rest, post)
def order(t):
    return [b[0] for b in split(t)[2]]
