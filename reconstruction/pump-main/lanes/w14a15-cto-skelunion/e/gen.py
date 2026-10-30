# gene library for skelunion: G[name] = list of (old,new); mk('p1_e3_tu8_s1') -> EDITS in ORDER
import sys,os
G={}
_S='let shared=a.sharing_config.key()==a.bonding_curve.creator&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();'
_H='let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;'
G['p1']=[(_S+_H,_H+'let shared=a.bonding_curve.creator==a.sharing_config.key()&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();')]
G['p2']=[(_S+_H,_H+_S)]
_EX='->Result<()>{ let a=&ctx.accounts;'
_EH='let hopt=holder;let holder=hopt==Some(true);'
_VH='->Result<Pubkey>{let holder=hopt==Some(true);'
_289='&&!(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}'
G['e3']=[(_EX,'->Result<()>{ let hb=holder.unwrap_or(false);let a=&ctx.accounts;'),(_EH,'let hopt=hb;let holder=hb;'),('fn validate(st:&CtoState,hopt:Option<bool>,','fn validate(st:&CtoState,hopt:bool,'),(_VH,'->Result<Pubkey>{let holder=hopt;'),(_289,'&&!hopt{return Err(error!(PumpError::HolderRewardCreatorImmutable));}')]
_T306='let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};'
G['tu8']=[(_T306,'let t=if unsafe{*(&new as *const Option<Pubkey> as *const u8)}&1!=0{unsafe{new.unwrap_unchecked()}}else{return Err(error!(PumpError::CtoNewCreatorRequired));};')]
# f2 = RAR + HB0 (w14a07)
G['rar']=[(';let args=&(new,);let sk=a.sharing_config.key();',';let sk=a.sharing_config.key();'),('&a.global);let (holder,cashback,target,sharing_update,collect_old,skip)={','&a.global);let args=&(new,);let (holder,cashback,target,sharing_update,collect_old,skip)={')]
G['hb0']=[('new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{','new:Option<Pubkey>,has:bool,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{'),("let t=if let Some(t)=new{t}else{","let t=if let (true,Some(t))=(has,new){t}else{"),("validate(&st,hopt,fee,new,","validate(&st,hopt,fee,new,args.0.is_some(),")]
# s1: sharing CPI all to_account_info
_SHPRE='  crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(a.pump_fees.to_account_info(),crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{pool_authority:{'
CALL='crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(a.pump_fees.to_account_info(),crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{pool_authority:a.pool_authority.to_account_info(),authority:a.admin_set_creator_authority.to_account_info(),global:a.global.to_account_info(),mint:a.mint.to_account_info(),sharing_config:a.sharing_config.to_account_info(),event_authority:a.pump_fees_event_authority.to_account_info(),program:a.pump_fees.to_account_info()},signer_seeds),val)'
def _s1(src):
    L=src.split('\n'); i=[k for k,l in enumerate(L) if l.startswith(_SHPRE)]; assert len(i)==1
    return [(L[i[0]],'  '+CALL+'?;')]
G['s1']=_s1
ORDER=['p1','p2','e3','tu8','rar','hb0','s1']
# external pools
sys.path.insert(0,os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w13a47-cto-stitch9/tools'))
try:
    import genes47 as _g47
    for _k,_v in _g47.G.items():
        if _v: G.setdefault('g.'+_k,_v)
except Exception as _e: print('genes47 import failed',_e,file=sys.stderr)
import json as _j
for _k in _j.load(open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/sizeknobs-cto.json'))['knobs']:
    if _k.get('edit'): G.setdefault('K.'+_k['name'],[(e['old'],e['new']) for e in _k['edit']])
def split(name):
    return name.split('+') if '+' in name else name.split('_') if all(x in ORDER for x in name.split('_')) else [name]
def mk(name,src):
    E=[]
    for n in sorted(split(name),key=lambda x:ORDER.index(x) if x in ORDER else 99):
        g=G[n]; E+=g(src) if callable(g) else g
    return E
# tail-decoupling partners (cashback/holder not long-lived)
G['cbR']=[('  curve.is_cashback_coin=cashback;\n','  if holder{curve.is_cashback_coin=false;}\n')]
G['cbR2']=[('  curve.is_cashback_coin=cashback;\n','  curve.is_cashback_coin=!holder&&curve.is_cashback_coin;\n')]
G['cbR3']=[('  curve.is_cashback_coin=cashback;\n','  curve.is_cashback_coin&=!holder;\n')]


# w14a10 e3 position variants (their p0..p3 renamed q0..q3; e3b/c/d)
_VB=[('fn validate(st:&CtoState,hopt:Option<bool>,','fn validate(st:&CtoState,hopt:bool,'),(_VH,'->Result<Pubkey>{let holder=hopt;'),(_289,'&&!hopt{return Err(error!(PumpError::HolderRewardCreatorImmutable));}')]
G['e3b']=[(_EH,'let hopt=holder.unwrap_or(false);let holder=hopt;')]+_VB
G['e3c']=[(_EH,'let hopt=holder==Some(true);let holder=hopt;')]+_VB
G['e3d']=[(_EH,'let hopt=matches!(holder,Some(true));let holder=hopt;')]+_VB
_EH3=(_EH,'let hopt=hb;let holder=hb;')
G['q1']=[('let mint=a.mint.key();','let mint=a.mint.key();let hb=holder.unwrap_or(false);'),_EH3]+_VB
G['q2']=[('holder_key=hk.0;','holder_key=hk.0;let hb=holder.unwrap_or(false);'),_EH3]+_VB
G['q3']=[('&a.global);let (holder,cashback,target,sharing_update,collect_old,skip)={','&a.global);let hb=holder.unwrap_or(false);let (holder,cashback,target,sharing_update,collect_old,skip)={'),_EH3]+_VB
ORDER+=['e3b','e3c','e3d','q1','q2','q3']

# partial s1: one sharing-CPI literal clone -> to_account_info
G['s_po']=[('pool_authority:{let x:&AccountInfo= a.pool_authority.as_ref();AccountInfo{executable:x.executable,lamports:x.lamports.clone(),data:x.data.clone(),is_writable:x.is_writable,owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,key:x.key}}','pool_authority:a.pool_authority.to_account_info()')]
G['s_gl']=[('global:{let x:&AccountInfo= a.global.as_ref().as_ref();AccountInfo{is_signer:x.is_signer,is_writable:x.is_writable,rent_epoch:x.rent_epoch,lamports:x.lamports.clone(),data:x.data.clone(),owner:x.owner,executable:x.executable,key:x.key}}','global:a.global.to_account_info()')]
G['s_mi']=[('mint:{let x:&AccountInfo= a.mint.as_ref();AccountInfo{rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable,lamports:x.lamports.clone(),owner:x.owner,data:x.data.clone(),key:x.key}}','mint:a.mint.to_account_info()')]
G['s_ev']=[('event_authority:{let x=&*a.pump_fees_event_authority;AccountInfo{lamports:x.lamports.clone(),data:x.data.clone(),key:x.key,owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}}','event_authority:a.pump_fees_event_authority.to_account_info()')]
G['s_pr']=[('program:{let x:&AccountInfo= a.pump_fees.as_ref();AccountInfo{owner:x.owner,lamports:x.lamports.clone(),rent_epoch:x.rent_epoch,is_signer:x.is_signer,executable:x.executable,data:x.data.clone(),key:x.key,is_writable:x.is_writable}}','program:a.pump_fees.to_account_info()')]
ORDER+=['s_po','s_gl','s_mi','s_ev','s_pr']


G['cs']=[('  curve.is_cashback_coin=cashback;\n  curve.is_holder_reward=holder;\n','  curve.is_holder_reward=holder;\n  curve.is_cashback_coin=cashback;\n')]
ORDER+=['cs']

G['ql']=[('let quote_locked=crate::pump_quote::global_quote(a.bonding_curve.quote_mint,&a.global);','let quote_locked={let q=a.bonding_curve.quote_mint;q==Pubkey::default()||q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(&q)};')]
ORDER.insert(0,'ql')

_CB='let cashback=!holder&&st.cashback;'
G['cb1']=[(_CB,'let cashback=st.cashback&&!holder;')]
G['cb2']=[(_CB,'let cashback=if holder{false}else{st.cashback};')]
G['cb3']=[(_CB,'let cashback=!holder&st.cashback;')]
G['q2c']=[('holder_key=hk.0;','holder_key=hk.0;let hb=holder==Some(true);'),_EH3]+_VB
G['q2d']=[('holder_key=hk.0;','holder_key=hk.0;let hb=matches!(holder,Some(true));'),_EH3]+_VB
G['q2u']=[('holder_key=hk.0;','holder_key=hk.0;let hb=holder.unwrap_or_default();'),_EH3]+_VB
ORDER+=['cb1','cb2','cb3','q2c','q2d','q2u']

_TX='{let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{key:x.key,owner:x.owner,lamports:x.lamports.clone(),data:x.data.clone(),rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}}'
G['tc']=[('CpiContext::new('+_TX,'CpiContext::new(a.pump_amm.to_account_info()')]
G['tp']=[('program:'+_TX,'program:a.pump_amm.to_account_info()')]
G['ta']=[("associated_token_program:{let x:&AccountInfo=a.associated_token_program.as_ref();AccountInfo{key:x.key,owner:x.owner,..x.clone()}}","associated_token_program:a.associated_token_program.to_account_info()")]
ORDER+=['tc','tp','ta']

_SHM='let shared=a.sharing_config.key()==a.bonding_curve.creator&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();'
G['shA']=[(_SHM,'let shared=a.sharing_config.owner==&FEES&&a.sharing_config.key()==a.bonding_curve.creator&&!a.sharing_config.data_is_empty();')]
G['shB']=[(_SHM,'let shared=a.sharing_config.key()==a.bonding_curve.creator&&!a.sharing_config.data_is_empty()&&a.sharing_config.owner==&FEES;')]
G['shC']=[(_SHM,'let shared=a.bonding_curve.creator==a.sharing_config.key()&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();')]
G['shD']=[(_SHM,'let shared=a.sharing_config.key()==a.bonding_curve.creator&&*a.sharing_config.owner==FEES&&!a.sharing_config.data_is_empty();')]
ORDER+=['shA','shB','shC','shD']

G['q4']=[('!a.sharing_config.data_is_empty();let holder_key;','!a.sharing_config.data_is_empty();let hb=holder.unwrap_or(false);let holder_key;'),_EH3]+_VB
G['q5']=[('let (holder,cashback,target,sharing_update,collect_old,skip)={ let st=CtoState{','let (holder,cashback,target,sharing_update,collect_old,skip)={ let hb=holder.unwrap_or(false);let st=CtoState{'),_EH3]+_VB
G['q6']=[('fee_configurable:a.global.creator_fee_configurable};','fee_configurable:a.global.creator_fee_configurable};let hb=holder.unwrap_or(false);'),_EH3]+_VB
ORDER+=['q4','q5','q6']
G['m']=[]
ORDER.insert(0,'m')
if __name__=='__main__':
    name,srcf,out=sys.argv[1:4]
    open(out,'w').write('EDITS='+repr(mk(name,open(srcf).read()))+'\n')
