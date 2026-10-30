import re
def edit(t):
    lines=t.split('\n')
    for i,l in enumerate(lines):
        if l.startswith('define') and '8swap_hop17h' in l:
            n=re.sub(r'ptr noalias ([^%]*)%a\b', r'ptr \1%a', l)
            assert n!=l, 'no change'
            lines[i]=n
    return '\n'.join(lines)
