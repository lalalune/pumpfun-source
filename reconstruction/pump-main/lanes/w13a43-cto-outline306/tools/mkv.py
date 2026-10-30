#!/usr/bin/env python3
# mkv.py <var> <gene,gene,...> : copy var/m3 -> var/<var> (fresh dir), apply genes (old,new) from G (each old must occur once)
import sys,subprocess,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w13a43-cto-outline306')
SIG='new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{'
HARM='CtoNewCreatorNotAllowed));}*holder_key}else{'
CMP='if t==*sharing||t==*holder_key{'
VAL='let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;'
HK='let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;'
HK0='let (holder_key,_)=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);'
QL='let quote_locked=crate::pump_quote::global_quote(a.bonding_curve.quote_mint,&a.global);'
STB='mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin'
L289="if st.holder_reward&&!(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}"
G={
 'N289':[(L289,"if st.holder_reward{if !holder{return Err(error!(PumpError::HolderRewardCreatorImmutable));}}")],
 'V2':[(SIG,'new:Option<Pubkey>,holder_key:Pubkey,sharing:Pubkey)->Result<Pubkey>{'),(HARM,'CtoNewCreatorNotAllowed));}holder_key}else{'),(CMP,'if t==sharing||t==holder_key{'),(VAL,'let mut target=validate(&st,hopt,fee,args.0,holder_key,sk)?;')],
 'V1':[(SIG,'new:Option<Pubkey>,holder_key:Pubkey,sharing:&Pubkey)->Result<Pubkey>{'),(HARM,'CtoNewCreatorNotAllowed));}holder_key}else{'),(CMP,'if t==*sharing||t==holder_key{'),(VAL,'let mut target=validate(&st,hopt,fee,args.0,holder_key,&sk)?;')],
 'VA':[(VAL,'let mut target=validate(&st,hopt,fee,args.0,&holder_key,&sk)?;')],
 'HK0':[(HK,HK0)],
 'RSH':[('let shared=a.bonding_curve.creator==a.sharing_config.key()&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();','let shared=if a.bonding_curve.creator==a.sharing_config.key(){a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty()}else{false};')],
 'RPA':[('let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();let pargs=(target,a.bonding_curve.is_holder_reward,fee);','let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();'),('signer_seeds),pargs.0,pargs.1,pargs.2)?;','signer_seeds),target,a.bonding_curve.is_holder_reward,fee)?;')],
 'RAR':[(';let args=&(new,);let sk=a.sharing_config.key();',';let sk=a.sharing_config.key();'),('&a.global);let (holder,cashback,target,sharing_update,collect_old,skip)={','&a.global);let args=&(new,);let (holder,cashback,target,sharing_update,collect_old,skip)={')],
 'RTU':[('let (collect_old,sharing_update,skip)=if shared{if holder{(false,Some(None),false)}else{target=st.creator;(false,Some(args.0),true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};','let (sharing_update,collect_old,skip)=if shared{if holder{(Some(None),false,false)}else{target=st.creator;(Some(args.0),false,true)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)};')],
 'AR':[('let args=&(new,);','let args=&new;'),('(false,Some(args.0),true)','(false,Some(*args),true)')],
 'AN':[('let args=&(new,);',''),('(false,Some(args.0),true)','(false,Some(new),true)')],
 'B3':[(QL,'let (cb0,hr0,my0)=(a.bonding_curve.is_cashback_coin,a.bonding_curve.is_holder_reward,a.bonding_curve.is_mayhem_mode);'+QL),(STB,'mayhem:my0,holder_reward:hr0,cashback:cb0')],
}
v=sys.argv[1]; d=f'{O}/var/{v}'
assert not os.path.exists(d), d+' exists'
subprocess.run(['rsync','-a',f'{O}/var/'+os.environ.get('MKV_BASE','m3')+'/',d+'/'],check=True)
p=d+'/src/creator/admin_cto.rs'; s=open(p).read()
for g in (sys.argv[2].split(',') if len(sys.argv)>2 and sys.argv[2] else []):
    for a,b in G[g]:
        assert s.count(a)==1,(g,a[:60]); s=s.replace(a,b)
open(p,'w').write(s)
print(v,'ok')
