import re
PAT=re.compile(r'admin_cto7execute|AccountInfo\$u20\$as\$u20\$core\.\.clone|to_account_info|ToAccountInfo|alloc\.\.rc\.\.Rc.*Clone|10inc_strong|AsRef')
def f(t):
    out=[]
    for l in t.split('\n'):
        if (l.startswith('define ') or l.startswith('declare ')) and PAT.search(l):
            l=re.sub(r'ptr noalias (nocapture )?noundef (readonly )?', lambda m:'ptr '+(m.group(1) or '')+'noundef '+(m.group(2) or ''), l)
        out.append(l)
    return '\n'.join(out)
EDITS=[f]
