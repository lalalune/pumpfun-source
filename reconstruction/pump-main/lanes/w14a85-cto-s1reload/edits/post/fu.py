import os
# fake use(s) of swept: FU env = comma list of positions: cpi (before sharing CPI call), arm (bb36 entry), mid (before clone 5 acc reload)
P=os.environ.get('FU','cpi').split(',')
U='  call void asm sideeffect "", "r"(i64 %_95.sroa.0.0)\n'
def f(t):
    if 'cpi' in P:
        k=t.index('  %670 = call { i64, ptr } @_ZN14pump_recovered9pump_fees3cpi24admin_cto_sharing_config'); t=t[:k]+U+t[k:]
    if 'arm' in P:
        k=t.index('bb36:'); k=t.index('\n',k)+1; t=t[:k]+U+t[k:]
    if 'mid' in P:
        k=t.index('  %acr.5 = load'); t=t[:k]+U+t[k:]
    return t
EDITS=[f]
