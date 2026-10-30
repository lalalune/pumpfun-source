HK='let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;'
HK0='let (holder_key,_)=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);'
ARGS='let args=&(new,);'
VAL='let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;'
STE='fee_configurable:a.global.creator_fee_configurable};'
SIG='new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{'
HARM='CtoNewCreatorNotAllowed));}*holder_key}else{'
CMP='if t==*sharing||t==*holder_key{'
SHARM='(Some(args.0),false,true)'
# v1: holder_key by value
V1=[(SIG,'new:Option<Pubkey>,holder_key:Pubkey,sharing:&Pubkey)->Result<Pubkey>{'),(HARM,'CtoNewCreatorNotAllowed));}holder_key}else{'),(CMP,'if t==*sharing||t==holder_key{')]
def val(newx='new',hk='&holder_key',sk='&sk'):
    return 'let mut target=validate(&st,hopt,fee,%s,%s,%s)?;'%(newx,hk,sk)
SKL='let sk=a.sharing_config.key();'
# V3: new, sharing, holder_key all by value, sharing evaluated inline (orig copy order new, sk, hk)
V3=[(SIG,'new:Option<Pubkey>,sharing:Pubkey,holder_key:Pubkey)->Result<Pubkey>{'),(HARM,'CtoNewCreatorNotAllowed));}holder_key}else{'),(CMP,'if t==sharing||t==holder_key{'),(SKL,'')]
VAL3=lambda n: 'let mut target=validate(&st,hopt,fee,%s,a.sharing_config.key(),holder_key)?;'%n
# V2: both by value, original param order (new, holder_key, sharing), sk let kept
V2=[(SIG,'new:Option<Pubkey>,holder_key:Pubkey,sharing:Pubkey)->Result<Pubkey>{'),(HARM,'CtoNewCreatorNotAllowed));}holder_key}else{'),(CMP,'if t==sharing||t==holder_key{')]
QL='let quote_locked=crate::pump_quote::global_quote(a.bonding_curve.quote_mint,&a.global);'
STL='let st=CtoState{creator:a.bonding_curve.creator,max_fee:a.global.max_configurable_creator_fee_bps,mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin,quote_locked,holder_enabled:a.global.is_holder_reward_enabled,fee_configurable:a.global.creator_fee_configurable};'
GQ='quote_locked:crate::pump_quote::global_quote(a.bonding_curve.quote_mint,&a.global)'
def stl(order):
    f={'creator':'creator:a.bonding_curve.creator','max_fee':'max_fee:a.global.max_configurable_creator_fee_bps','mayhem':'mayhem:a.bonding_curve.is_mayhem_mode','holder_reward':'holder_reward:a.bonding_curve.is_holder_reward','cashback':'cashback:a.bonding_curve.is_cashback_coin','quote_locked':GQ,'holder_enabled':'holder_enabled:a.global.is_holder_reward_enabled','fee_configurable':'fee_configurable:a.global.creator_fee_configurable'}
    return 'let st=CtoState{'+','.join(f[k] for k in order)+'};'
T8=V2+[(ARGS,''),(VAL,val('args.0','holder_key','sk')),(HK,HK0)]
IN296=[(" if holder&&!st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}\n\n let target=if holder{if new"," let target=if holder{if !st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}\n\n  if new")]
