"""edit_move.py (ctoracle --edit): MOVE='<value>@<label substring>[@before:<value>]' moves the def line of <value> to the top of
the first block whose label contains the substring (after phis), or right before the def of another value."""
import re, os
def edit(f):
    L = f.split('\n')
    for spec in os.environ['MOVE'].split(';'):
        if not spec: continue
        parts = spec.split('@'); v = parts[0]
        k = [i for i, l in enumerate(L) if re.match(r'  %' + re.escape(v) + r' = ', l)][0]
        line = L.pop(k)
        if len(parts) > 2 and parts[2].startswith('before:'):
            w = parts[2][7:]; d = [i for i, l in enumerate(L) if re.match(r'  %' + re.escape(w) + r' = ', l)][0]
        else:
            b = [i for i, l in enumerate(L) if re.match(r'^\S.*:', l) and parts[1] in l.split(':')[0]][0]; d = b + 1
            while re.match(r'  %\S+ = phi ', L[d]): d += 1
        L.insert(d, line)
    s = '\n'.join(L)
    order = [m.group(1) for m in re.finditer(r'^  %(\d+) = ', s, re.M)]
    mp = dict(zip(order, sorted(order, key=int)))
    s = re.sub(r'%(\d+)(?![\w.$-])', lambda m: '%__' + mp[m.group(1)] if m.group(1) in mp else m.group(0), s)
    return s.replace('%__', '%')
