SH='a.sharing_config.key()==a.bonding_curve.creator&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();'
G={
'hL':[(SH,'a.bonding_curve.creator==a.sharing_config.key()&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();')],
'kd':[(SH,'*a.sharing_config.key==a.bonding_curve.creator&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();')],
'kr':[(SH,'a.sharing_config.key==&a.bonding_curve.creator&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();')],
'kdL':[(SH,'a.bonding_curve.creator==*a.sharing_config.key&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();')],
'krL':[(SH,'&a.bonding_curve.creator==a.sharing_config.key&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();')],
'sci':[(SH,'{let s=&a.sharing_config;s.key()==a.bonding_curve.creator&&s.owner==&FEES&&!s.data_is_empty()};')],
'sciL':[(SH,'{let s:&AccountInfo=a.sharing_config.as_ref();a.bonding_curve.creator==*s.key&&s.owner==&FEES&&!s.data_is_empty()};')],
'ownd':[(SH,'a.sharing_config.key()==a.bonding_curve.creator&&*a.sharing_config.owner==FEES&&!a.sharing_config.data_is_empty();')],
'skl':[(SH,'{let sk=a.sharing_config.key();sk==a.bonding_curve.creator}&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();')],
'crl':[(SH,'{let cr=a.bonding_curve.creator;a.sharing_config.key()==cr}&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();')],
'crr':[(SH,'{let cr=&a.bonding_curve.creator;a.sharing_config.key()==*cr}&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();')],
'peq':[(SH,'a.sharing_config.key().eq(&a.bonding_curve.creator)&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();')],
'mintd':[('let mint=a.mint.key();','let mint=*a.mint.key;')],
'mintk':[('let mint=a.mint.key();','let mint=a.mint.to_account_info().key;let mint=*mint;')],
'seedk':[('find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID)','find_program_address(&[b"holder-rewards",a.mint.key.as_ref()],&crate::ID)')],
'seeda':[('find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID)','find_program_address(&[b"holder-rewards".as_ref(),mint.as_ref()],&crate::ID)')],
'seedr':[('find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID)','find_program_address(&[&b"holder-rewards"[..],&mint.to_bytes()],&crate::ID)')],
'hkd':[('let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;','let holder_key=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID).0;')],
'hkt':[('let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;','let (holder_key,_)=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);')],
'hkb':[('holder_key=hk.0;','holder_key={hk}.0;')],
'qlr':[('let q=a.bonding_curve.quote_mint;q==Pubkey::default()||q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(&q)','let q=&a.bonding_curve.quote_mint;*q==Pubkey::default()||*q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(q)')],
'mintpid':[('mint.as_ref()],&crate::ID)','mint.as_ref()],ctx.program_id)')],
}
PDA='let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;'
QL='let quote_locked={let q=a.bonding_curve.quote_mint;q==Pubkey::default()||q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(&q)};'
G.update({
'sdl':[(PDA,'let holder_key;let seeds:&[&[u8]]=&[b"holder-rewards",mint.as_ref()];let hk=Pubkey::find_program_address(seeds,&crate::ID);holder_key=hk.0;')],
'sda':[(PDA,'let holder_key;let seeds=[b"holder-rewards".as_ref(),mint.as_ref()];let hk=Pubkey::find_program_address(&seeds,&crate::ID);holder_key=hk.0;')],
'hkty':[(PDA,'let holder_key:Pubkey;let hk:(Pubkey,u8)=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;')],
'hkblk':[(PDA,'let holder_key;{let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;}')],
'hkblk2':[(PDA,'let holder_key={let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);hk.0};')],
'hklate':[(PDA+QL,'let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);'+QL+'holder_key=hk.0;')],
'hkmut':[(PDA,'let mut holder_key=Pubkey::default();let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;')],
'hkpair':[(PDA,'let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);let (k,_b)=hk;holder_key=k;')],
'hkcp':[(PDA,'let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=Pubkey::new_from_array(hk.0.to_bytes());')],
'mintlate':[('let mint=a.mint.key();let shared=','let shared='),('let holder_key;let hk=','let mint=a.mint.key();let holder_key;let hk=')],
'shlate':[('let shared='+SH+PDA, PDA+'let shared='+SH)] if False else [],
'shqm':[('let shared='+SH,''),(QL,QL+'let shared='+SH)],
})
G.update({
'pda':[('let shared='+SH+PDA, PDA+'let shared='+SH)],
'fl':[(QL,'let (cb0,hr0,my0)=(a.bonding_curve.is_cashback_coin,a.bonding_curve.is_holder_reward,a.bonding_curve.is_mayhem_mode);'+QL),
      ('mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin','mayhem:my0,holder_reward:hr0,cashback:cb0')],
'hkc':[('validate(&st,hopt,fee,new,&holder_key,&sk)','validate(&st,hopt,fee,new,&{holder_key},&sk)')],
})
G['pdaL']=G['pda']+[]  # placeholder
import json as _j,os as _o
_kf=_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),'knobs.json')
if _o.path.exists(_kf):
    for _k,_v in _j.load(open(_kf)).items(): G['k_'+_k]=[tuple(x) for x in _v]
_STC='let st=CtoState{creator:a.bonding_curve.creator,max_fee:a.global.max_configurable_creator_fee_bps,'
G.update({
'cr1':[(_STC,'let st=CtoState{creator:a.bonding_curve.creator.clone(),max_fee:a.global.max_configurable_creator_fee_bps,')],
'cr2':[(_STC,'let st=CtoState{creator:Pubkey::new_from_array(a.bonding_curve.creator.to_bytes()),max_fee:a.global.max_configurable_creator_fee_bps,')],
'cr3':[(_STC,'let st=CtoState{max_fee:a.global.max_configurable_creator_fee_bps,'),('fee_configurable:a.global.creator_fee_configurable};','fee_configurable:a.global.creator_fee_configurable,creator:a.bonding_curve.creator};')],
'cr4':[(_STC,'let st=CtoState{creator:{let c=&a.bonding_curve.creator;*c},max_fee:a.global.max_configurable_creator_fee_bps,')],
'cr5':[(_STC,'let cr=a.bonding_curve.creator;let st=CtoState{creator:cr,max_fee:a.global.max_configurable_creator_fee_bps,')],
})
