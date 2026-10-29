"""Alphabetical-mount fixes (line-neutral). usage: order3.py <src>"""
import sys,re
from pathlib import Path
S=Path(sys.argv[1])
def rd(p): return (S/p).read_text().split('\n')
def wr(p,L): (S/p).write_text('\n'.join(L))
def find(L,pat,start=0):
    for i in range(start,len(L)):
        if re.search(pat,L[i]): return i
    raise SystemExit('nf '+pat)
lib=rd('lib.rs')
# (e) idl_authority (admin_set_idl_authority.rs) mounted first
i=find(lib,r'^#\[path="admin_set_idl_authority.rs"\]pub mod idl_authority;$'); lib[i]=''
lib[0]='#[path="admin_set_idl_authority.rs"]pub mod idl_authority;'+lib[0]
# (f) mayhem_virtual_params mounted after fee_recipient (file order: extend_account, fee_recipient, mayhem_virtual_params, migrate)
i=find(lib,r'^pub mod mayhem_virtual_params;$'); lib[i]=''
i=find(lib,r'^#\[path="extend_account.rs"\]pub mod extend;'); lib[i]+='pub mod mayhem_virtual_params;'
# (g) BondingCurve::sync_virtual_quote_reserves right after reserved_bonding_curve_fees (lib.rs)
mv=rd('mayhem_virtual_params.rs'); s=find(mv,r'^impl BondingCurve \{$'); e=find(mv,r'^}$',s)
blk=[x.replace('impl BondingCurve {','impl crate::trade_types::BondingCurve {') for x in mv[s:e+1]]
mv[s:e+1]=['']*(e-s+1); wr('mayhem_virtual_params.rs',mv)
r=find(lib,r'^pub fn reserved_bonding_curve_fees'); r=find(lib,r'^}$',r)+1
j=find(lib,r'^// layout-pad',r)+1
assert all(lib[j+k].strip()=='' for k in range(len(blk))), 'not enough pad'
for k,x in enumerate(blk): lib[j+k]=x
wr('lib.rs',lib); print('ok', len(blk))
