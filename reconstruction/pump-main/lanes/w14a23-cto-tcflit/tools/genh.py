#!/usr/bin/env python3
"""genh.py <outdir>: hoist variants: bind the account's &AccountInfo before the TCF CPI call and clone it in place.
name h_<acct> ; hx_<acct> = bind before the data_is_empty test (outside the else-if arm, same line)."""
import sys,os
sys.path.insert(0,os.path.dirname(__file__))
from gen import ACC
HEAD='else if !a.coin_creator_vault_ata.data_is_empty(){crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2('
d=sys.argv[1]; os.makedirs(d,exist_ok=True)
for k,(f,e,r) in ACC.items():
    E=[(HEAD,HEAD.replace('{crate::','{let hp:&AccountInfo='+r+';crate::')),(f+':'+e+'.to_account_info()',f+':hp.clone()')]
    open(f'{d}/h_{k}.py','w').write('''E=%r
def T(s):
    i=s.index('else if !a.coin_creator_vault_ata.data_is_empty(){crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2('); j=s.index('\\n',i)
    seg=s[i:j]
    for a,b in E:
        assert seg.count(a)==1,(a,seg.count(a)); seg=seg.replace(a,b)
    return s[:i]+seg+s[j:]
'''%E)
