import os
R=os.environ.get('R','r9')
MODE=os.environ.get('MODE','pin')
def edit(fn):
    lines=fn.split('\n')
    s=next(i for i,l in enumerate(lines) if l.startswith('bb83:'))
    # after phis
    k=s+1
    while ' = phi ' in lines[k]: k+=1
    if MODE=='pin':
        lines.insert(k,f'  %pinv = call i64 asm sideeffect "$0 = 0", "={{{R}}}"()')
    elif MODE=='swept':
        # route swept through r9: tie the phi value into a register-constrained asm copy
        lines.insert(k,f'  %sw9 = call i64 asm sideeffect "$0 = $1", "={{{R}}},{{{R}}}"(i64 %_79.sroa.0.0)')
    e=next(i for i,l in enumerate(lines) if 'store i64 %_79.sroa.0.0, ptr %703' in l)
    if MODE=='pin':
        lines.insert(e,f'  call void asm sideeffect "", "{{{R}}}"(i64 %pinv)')
    else:
        lines[e]=lines[e].replace('store i64 %_79.sroa.0.0','store i64 %sw9')
    return '\n'.join(lines)
