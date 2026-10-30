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
