import re
def _lines(t): return t.split('\n')
def _uses(L, var, start):
    pat = re.compile(re.escape(var) + r'(?![\w.])')
    return [i for i in range(start, len(L)) if pat.search(L[i]) and not L[i].lstrip().startswith(var + ' =')]
def via_slot(var, keep=1, tag='s', store_at=None, align=8, ty='ptr'):
    """store var into a fresh alloca right after its def; all uses except the first `keep` load it back."""
    def f(t):
        L = _lines(t); pat = re.compile(re.escape(var) + r'(?![\w.])')
        d = next(i for i, l in enumerate(L) if l.lstrip().startswith(var + ' ='))
        us = _uses(L, var, d + 1)
        ent = next(i for i, l in enumerate(L) if '%_11.i269 = alloca' in l)
        for n, u in enumerate(reversed(us[keep:])):
            v = f'%{tag}r{n}'
            L[u] = pat.sub(v, L[u]); L.insert(u, f'  {v} = load {ty}, ptr %{tag}slot, align 8')
        L.insert(d + 1 if store_at is None else store_at, f'  store {ty} {var}, ptr %{tag}slot, align 8')
        L.insert(ent, f'  %{tag}slot = alloca [8 x i8], align 8')
        return '\n'.join(L)
    return f
def remat(var, keep=1, tag='g'):
    """recompute var's GEP before each use except the first `keep`."""
    def f(t):
        L = _lines(t); pat = re.compile(re.escape(var) + r'(?![\w.])')
        d = next(i for i, l in enumerate(L) if l.lstrip().startswith(var + ' ='))
        rhs = L[d].split('=', 1)[1]
        us = _uses(L, var, d + 1)
        for n, u in enumerate(reversed(us[keep:])):
            v = f'%{tag}r{n}'
            L[u] = pat.sub(v, L[u]); L.insert(u, f'  {v} ={rhs}')
        return '\n'.join(L)
    return f
