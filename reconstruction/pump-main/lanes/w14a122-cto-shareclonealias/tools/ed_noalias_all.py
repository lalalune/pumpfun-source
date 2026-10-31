import re
def f(t):
    out=[]
    for l in t.split('\n'):
        if l.startswith('define ') or l.startswith('declare '):
            l=re.sub(r'ptr noalias (nocapture )?noundef readonly', lambda m:'ptr '+(m.group(1) or '')+'noundef readonly', l)
        out.append(l)
    return '\n'.join(out)
EDITS=[f]
