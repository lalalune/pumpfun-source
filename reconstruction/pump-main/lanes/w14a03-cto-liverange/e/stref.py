# generator: T(s) makes CtoState fields in FIELDS references (re-read at use)
import re, os
FIELDS = os.environ.get('STREF', 'max_fee').split(',')
TY = {'creator':'Pubkey','max_fee':'u64'}
def T(s):
    for f in FIELDS:
        ty = TY.get(f, 'bool')
        a = 'struct CtoState{' if 'struct CtoState{' in s else "struct CtoState<'g>{"
        s = s.replace(a, "struct CtoState<'g>{", 1)
        s = s.replace("<'g>{" , "<'g>{", 1)
        old = '%s:%s,' % (f, ty) if f != 'fee_configurable' else '%s:%s}' % (f, ty)
        new = "%s:&'g %s," % (f, ty) if f != 'fee_configurable' else "%s:&'g %s}" % (f, ty)
        assert s.count(old) >= 1, old
        i = s.index('struct CtoState'); j = s.index('}', i) + 1
        s = s[:i] + s[i:j].replace(old, new, 1) + s[j:]
        s = s.replace('fn validate(st:&CtoState,', "fn validate(st:&CtoState<'_>,")
        # initializer: f:EXPR (in the literal)
        lit = s.index('let st=CtoState{'); lend = s.index('};', lit)
        body = s[lit:lend]
        m = re.search(r'\b%s:([^,}]+)' % f, body); assert m, f
        expr = m.group(1)
        if f == 'quote_locked': raise SystemExit('no')
        body = body[:m.start()] + '%s:&%s' % (f, expr) + body[m.end():]
        s = s[:lit] + body + s[lend:]
        n0 = len(re.findall(r'\bst\.%s\b' % f, s))
        s = re.sub(r'(?<![\w*])st\.%s\b' % f, '(*st.%s)' % f, s)
    return s
