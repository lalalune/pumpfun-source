"""Line-neutral module mount/relocation fixes toward the original def order. usage: order2.py <src> [a][b][c][d]"""
import sys,re
from pathlib import Path
S=Path(sys.argv[1]); sel=sys.argv[2] if len(sys.argv)>2 else 'abcd'
def rd(p): return (S/p).read_text().split('\n')
def wr(p,L): (S/p).write_text('\n'.join(L))
def find(L,pat,start=0):
    for i in range(start,len(L)):
        if re.search(pat,L[i]): return i
    raise SystemExit('nf '+pat)
def put(L,i,lines):
    while any(L[i+k].strip() for k in range(len(lines))): i+=1
    for k,x in enumerate(lines): L[i+k]=x
lib=rd('lib.rs')
if 'a' in sel:
    i=find(lib,r'^#\[path="util/constant_product.rs"\] pub mod constant_product;$'); lib[i]+=' #[path="util/fee.rs"] pub mod fee_math;'
    sl=rd('sell.rs'); i=find(sl,r'#\[path="util/fee.rs"\] pub mod fee_math;'); sl[i]=sl[i].replace('#[path="util/fee.rs"] pub mod fee_math;','pub use crate::fee_math;'); wr('sell.rs',sl)
    fc=rd('fee_cpi.rs'); s=find(fc,r'^/// Shared fee query'); e=find(fc,r'^}',s)
    body=fc[s:e+1]; fc[s:e+1]=['']*(e-s+1); fc[s]='pub use crate::fee_math::trade_fees;'; wr('fee_cpi.rs',fc)
    rep=[('super::LegacyFeeConfig','crate::legacy_sell::LegacyFeeConfig'),('super::LegacyFeesProgram','crate::legacy_sell::LegacyFeesProgram'),
         ("InterfaceAccount<'info, Mint>","InterfaceAccount<'info, anchor_spl::token_interface::Mint>"),
         ('get_fees_with_quote_mint(CpiContext','crate::pump_fees::cpi::get_fees_with_quote_mint(CpiContext'),
         ('        GetFeesWithQuoteMint {','        crate::pump_fees::cpi::accounts::GetFeesWithQuoteMint {')]
    out=[]
    for x in body:
        for a,b in rep: x=x.replace(a,b)
        out.append(x)
    fe=rd('util/fee.rs'); j=find(fe,r'^// layout-pad: aligns the next Source site with the original line$')+1; put(fe,j,out); wr('util/fee.rs',fe)
if 'b' in sel:
    i=find(lib,r'^#\[path="util/account_name.rs"\] pub mod account_name;$'); lib[i]=''
    lib[0]='#[path="util/account_name.rs"] pub mod account_name;'+lib[0]
if 'c' in sel:
    sl=rd('sell.rs'); assert sl[0]=='#[path = "fee_recipient.rs"]' and sl[1]=='pub(crate) mod fee_recipient;'
    sl[0]='pub(crate) use crate::fee_recipient;'; sl[1]=''; wr('sell.rs',sl)
    i=find(lib,r'^#\[path="extend_account.rs"\]pub mod extend;$'); lib[i]+='#[path = "fee_recipient.rs"] pub(crate) mod fee_recipient;'
if 'd' in sel:
    tt=rd('trade_types.rs'); s=find(tt,r'^pub fn prepare_bonding_curve')-1; e=find(tt,r'^}',s)
    assert tt[s]=='#[inline(never)]'
    body=[x.replace("Account<'info, BondingCurve>","Account<'info, crate::trade_types::BondingCurve>") for x in tt[s:e+1]]
    tt[s:e+1]=['']*(e-s+1); tt[s]='pub use crate::extend::prepare_bonding_curve;'; wr('trade_types.rs',tt)
    ex=rd('extend_account.rs'); f=find(ex,r'^pub fn fund_bonding_curve_rent'); 
    k=f-1
    while ex[k-1].strip()=='' : k-=1
    # k = first blank line after execute's helpers; place body there
    put(ex,k+1,body); wr('extend_account.rs',ex)
wr('lib.rs',lib); print('ok',sel)
