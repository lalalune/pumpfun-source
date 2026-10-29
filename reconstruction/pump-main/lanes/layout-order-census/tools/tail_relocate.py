"""Line-neutral relocation of tail items. usage: tail1.py <src dir> [--wrap]"""
import sys,re
from pathlib import Path
S=Path(sys.argv[1]); WRAP='--wrap' in sys.argv
def rd(p): return (S/p).read_text().split('\n')
def wr(p,L): (S/p).write_text('\n'.join(L))
def find(L,pat,start=0):
    for i in range(start,len(L)):
        if re.search(pat,L[i]): return i
    raise SystemExit('nf '+pat)
def take(L,i,j,repl=''):
    """remove lines i..j (0-based incl), leave blanks; first line := repl"""
    t=L[i:j+1]; L[i:j+1]=['']*(j-i+1); L[i]=repl; return t
def put(L,i,lines):
    while any(L[i+k].strip() for k in range(len(lines))): i+=1
    for k,x in enumerate(lines):
        assert L[i+k].strip()=='', (i+k,L[i+k]); L[i+k]=x
lib=rd('lib.rs')
# --- events after TradeEvent
tt=rd('trade_types.rs'); i=find(tt,r'^pub struct CompleteEvent'); ce=take(tt,i-2,i,'pub use crate::CompleteEvent;'); wr('trade_types.rs',tt)
tv=rd('trade_v3.rs'); i=find(tv,r'pub struct PostCompleteBuyEvent'); pe=take(tv,i-1,i,'pub use crate::PostCompleteBuyEvent;'); wr('trade_v3.rs',tv)
sp=rd('set_params.rs'); i=find(sp,r'^pub struct SetParamsEvent'); se=take(sp,i-2,i,'pub use crate::SetParamsEvent;'); wr('set_params.rs',sp)
te=find(lib,r'^pub struct TradeEvent'); te_end=find(lib,r'^}',te)
put(lib,te_end+2,ce+pe+se)
# --- AdminGlobal between Initialize and Create
ag=find(lib,r'^pub struct AdminGlobal'); ag_end=find(lib,r'^}',ag)
agl=take(lib,ag-2,ag_end)
ini=find(lib,r'^pub struct Initialize'); ini_end=find(lib,r'^}',ini)
put(lib,ini_end+2,agl)
# --- LegacySell after LegacyBuy (into the freed AdminGlobal lines)
sl=rd('sell.rs'); i=find(sl,r'^pub struct LegacySell'); j=find(sl,r'^}',i)
lsl=take(sl,i-1,j,'pub use crate::LegacySell;'); wr('sell.rs',sl)
lsl=[x.replace("Account<'info,BondingCurve>","Account<'info,trade_types::BondingCurve>").replace("InterfaceAccount<'info,Mint>","InterfaceAccount<'info,anchor_spl::token_interface::Mint>").replace("InterfaceAccount<'info,TokenAccount>","InterfaceAccount<'info,anchor_spl::token_interface::TokenAccount>").replace("Interface<'info,TokenInterface>","Interface<'info,anchor_spl::token_interface::TokenInterface>").replace("Account<'info,LegacyFeeConfig>","Account<'info,legacy_sell::LegacyFeeConfig>").replace("Program<'info,LegacyFeesProgram>","Program<'info,legacy_sell::LegacyFeesProgram>") for x in lsl]
lb=find(lib,r'^pub struct LegacyBuy'); lb_end=find(lib,r'^}',lb)
put(lib,lb_end+2,lsl)
if WRAP:
    cr=find(lib,r'^pub struct Create<'); s=cr-2  # #[event_cpi] line
    assert lib[s].startswith('#[event_cpi]'),lib[s]
    lib[s]='pub mod bonding_curve_instruction_accounts{use super::*;'+lib[s]
    e=find(lib,r'^}',find(lib,r'^pub struct LegacySell'))
    lib[e]=lib[e]+'}pub use bonding_curve_instruction_accounts::*;'
# --- move-outs: AdminReadonly -> end sell_v2.rs ; UpdateGlobalAuthority -> end global_init.rs ; CloseUserVolume -> end claim_token_incentives.rs
def grab(name):
    i=find(lib,r'^pub struct '+name+r'<'); j=find(lib,r'^}',i); return take(lib,i-2,j)
def append(p,lines):
    L=rd(p)
    while L and L[-1]=='': L.pop()
    L+=lines; L.append(''); wr(p,L)
ar=grab('AdminReadonly'); append('sell_v2.rs',[x.replace('Account<\'info,Global>','Account<\'info,crate::Global>').replace('PumpError::','crate::PumpError::') for x in ar])
ug=grab('UpdateGlobalAuthority'); append('global_init.rs',[x.replace('Account<\'info,Global>','Account<\'info,crate::Global>').replace('PumpError::','crate::PumpError::') for x in ug])
cu=grab('CloseUserVolume'); append('token_incentives/claim_token_incentives.rs',[x.replace('Account<\'info,UserVolumeAccumulator>','Account<\'info,crate::UserVolumeAccumulator>') for x in cu])
# CollectCreatorFee -> start of collect_creator_fee.rs (one line, appended to line 2); event -> EOF
cc=grab('CollectCreatorFee')
i=find(lib,r'^pub struct CollectCreatorFeeEvent'); cev=take(lib,i-2,i)
def oneline(lines):
    out=[]
    for x in lines:
        x=x.strip()
        m=re.match(r'///\s*(.*)',x)
        if m: x='#[doc="'+m.group(1).replace('"','\\"')+'"]'
        out.append(x)
    return ''.join(out)
cf=rd('creator/collect_creator_fee.rs'); assert cf[1].startswith('use crate::CollectCreatorFeeEvent;')
cf[1]='use crate::CollectCreatorFeeEvent;'+oneline(cc); wr('creator/collect_creator_fee.rs',cf)
append('creator/collect_creator_fee.rs',[x.replace('pub struct CollectCreatorFeeEvent','pub struct CollectCreatorFeeEvent') for x in cev])
cf=rd('creator/collect_creator_fee.rs'); cf[1]=cf[1].replace('use crate::CollectCreatorFeeEvent;',''); wr('creator/collect_creator_fee.rs',cf)
wr('lib.rs',lib)
# --- rqal into pump_token_ext
mv=rd('migrate_v2.rs'); i=find(mv,r'^pub fn required_quote_account_len'); j=find(mv,r'^}',i)
rq=take(mv,i-1,j,'pub use pump_token_ext::required_quote_account_len;'); wr('migrate_v2.rs',mv)
pt=(S.parent/'pump-token-ext/src/lib.rs'); P=pt.read_text().split('\n')
q=next(k for k,x in enumerate(P) if x.startswith('pub fn quote_extensions_supported'))-1
qend=next(k for k in range(len(P)-1,0,-1) if P[k].startswith('}'))
block=P[q:qend+1]; del P[q:qend+1]
first=next(k for k,x in enumerate(P) if x.startswith('/// Native fee schedule'))
P[first:first]=block+['']+rq+['']
pt.write_text('\n'.join(P))
print('ok')
