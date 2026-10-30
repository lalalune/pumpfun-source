import re,os
K=int(os.environ['K'])
def edit(t):
    lines=t.split('\n')
    s=[i for i,l in enumerate(lines) if l.startswith('define') and '8swap_hop17h' in l][0]
    e=s
    while lines[e]!='}': e+=1
    n=0
    for j in range(s+1,e):
        l=lines[j]
        if re.search(r'\b(call|invoke)\b.*@_ZN',l) and 'llvm.' not in l:
            n+=1
            if n==K:
                lines.insert(j,'  call void @w7_capture(ptr %a)'); break
    lines.append('declare void @w7_capture(ptr)')
    return '\n'.join(lines)
