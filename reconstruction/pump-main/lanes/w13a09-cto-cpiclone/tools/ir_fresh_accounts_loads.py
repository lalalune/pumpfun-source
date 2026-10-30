import re
OFF={'%577':152,'%588':104,'%_200':0,'%17':8,'%4':16,'%9':144,'%639':160}
def edit(fn):
    lines=fn.split('\n')
    s=next(i for i,l in enumerate(lines) if l.startswith('bb34:'))
    e=next(i for i,l in enumerate(lines) if 'call { i64, ptr } @_ZN14pump_recovered9pump_fees3cpi24admin_cto_sharing_config' in l)
    out=lines[:s]; n=0
    for i in range(s,e):
        l=lines[i]
        m=re.match(r'(\s+%\S+ = load ptr, ptr )(%[\w.]+)(, align 8, !nonnull !2, !align !3, !noundef !2)$',l)
        if m and m.group(2) in OFF:
            n+=1
            out.append(f'  %rl{n} = load ptr, ptr %3, align 8, !nonnull !2, !align !3, !noundef !2')
            out.append(f'  %rg{n} = getelementptr inbounds i8, ptr %rl{n}, i64 {OFF[m.group(2)]}')
            l=m.group(1)+f'%rg{n}'+m.group(3)
        out.append(l)
    out+=lines[e:]
    return '\n'.join(out)
