import os
RS=os.environ.get('RS','r9,r0').split(',')
def edit(fn):
    lines=fn.split('\n')
    s=next(i for i,l in enumerate(lines) if l.startswith('bb34:'))
    for k,R in enumerate(RS):
        lines.insert(s+1,f'  %pinv{k} = call i64 asm sideeffect "$0 = 0", "={{{R}}}"()')
    e=next(i for i,l in enumerate(lines) if 'call { i64, ptr } @_ZN14pump_recovered9pump_fees3cpi24admin_cto_sharing_config' in l)
    for k,R in enumerate(RS):
        lines.insert(e,f'  call void asm sideeffect "", "{{{R}}}"(i64 %pinv{k})')
    return '\n'.join(lines)
