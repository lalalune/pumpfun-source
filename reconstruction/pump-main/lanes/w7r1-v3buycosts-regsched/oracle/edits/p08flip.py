import re
def edit(f):
    L=f.split('\n')
    for i,l in enumerate(L):
        if '%_11.sroa.0.2 = phi' in l:
            L[i]=l.replace('[ false,','[ TMP,').replace('[ true,','[ false,').replace('[ TMP,','[ true,')
        m=re.match(r'^(\s*br i1 %_11.sroa.0.2, )label (\S+), label (\S+)$',l)
        if m: L[i]=m.group(1)+'label '+m.group(3)+', label '+m.group(2)
    return '\n'.join(L)
