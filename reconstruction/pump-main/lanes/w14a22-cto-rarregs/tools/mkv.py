#!/usr/bin/env python3
# mkv.py <var> <gene,gene,...> : copy var/m3 -> var/<var> (fresh dir), apply genes (old,new) from G (each old must occur once)
import sys,subprocess,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a22-cto-rarregs')
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
 'RAR':[(';let args=&(new,);let sk=a.sharing_config.key();',';let sk=a.sharing_config.key();'),('contains(&q)};let (holder,cashback,target,sharing_update,collect_old,skip)={','contains(&q)};let args=&(new,);let (holder,cashback,target,sharing_update,collect_old,skip)={')],
 'RTU':[('let (collect_old,sharing_update,skip)=if shared{if holder{(false,Some(None),false)}else{target=st.creator;(false,Some(args.0),true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};','let (sharing_update,collect_old,skip)=if shared{if holder{(Some(None),false,false)}else{target=st.creator;(Some(args.0),false,true)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)};')],
 'AR':[('let args=&(new,);','let args=&new;'),('(false,Some(args.0),true)','(false,Some(*args),true)')],
 'AN':[('let args=&(new,);',''),('(false,Some(args.0),true)','(false,Some(new),true)')],
 'VR':[(SIG,'new:&Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{'),('let t=if let Some(t)=new{t}else{','let t=if let Some(t)=*new{t}else{'),(VAL,'let mut target=validate(&st,hopt,fee,&args.0,&holder_key,&sk)?;')],
 'VR2':[(SIG,'new:&Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{'),('let t=if let Some(t)=new{t}else{','let t=if let Some(t)=*new{t}else{'),(VAL,'let mut target=validate(&st,hopt,fee,&new,&holder_key,&sk)?;')],
 'VC':[('Result<Pubkey>{let holder=hopt==Some(true);','Result<Pubkey>{let new=&new;let holder=hopt==Some(true);'),('let t=if let Some(t)=new{t}else{','let t=if let Some(t)=*new{t}else{')],
 'B3':[(QL,'let (cb0,hr0,my0)=(a.bonding_curve.is_cashback_coin,a.bonding_curve.is_holder_reward,a.bonding_curve.is_mayhem_mode);'+QL),(STB,'mayhem:my0,holder_reward:hr0,cashback:cb0')],
}

CF=(" Ok(target)}pub fn execute(", " Ok(target)}#[cold] fn cold(){}pub fn execute(")
G['C1']=[("let t=if let Some(t)=new{t}else{","let t=if let Some(t)=new{cold();t}else{"),CF]
G['C2']=[("if t==Pubkey::default(){return Err(","if t==Pubkey::default(){cold();return Err("),("if t==*sharing||t==*holder_key{return Err(","if t==*sharing||t==*holder_key{cold();return Err("),CF]
G['C3']=[("if t==Pubkey::default(){return Err(","if t==Pubkey::default(){cold();return Err("),CF]

SIGN=('new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{','new:Option<&Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{')
G['OR1']=[SIGN,("let t=if let Some(t)=new{cold();t}","let t=if let Some(&t)=new{cold();t}"),("validate(&st,hopt,fee,new,","validate(&st,hopt,fee,args.0.as_ref(),")]
G['OR2']=[SIGN,("let t=if let Some(t)=new{cold();t}","let t=if let Some(&t)=new{cold();t}"),("validate(&st,hopt,fee,new,","validate(&st,hopt,fee,new.as_ref(),")]
G['HB']=[('new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{','new:Option<Pubkey>,has:bool,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{'),("let t=if let Some(t)=new{cold();t}","let t=if has{cold();new.unwrap_or_default()}"),("validate(&st,hopt,fee,new,","validate(&st,hopt,fee,new,args.0.is_some(),")]

G['HB2']=[('new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{','new:Option<Pubkey>,has:bool,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{'),("let t=if let Some(t)=new{cold();t}else{","let t=if let (true,Some(t))=(has,new){cold();t}else{"),("validate(&st,hopt,fee,new,","validate(&st,hopt,fee,new,new.is_some(),")]

G['HB3']=[('new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{','new:Option<Pubkey>,has:bool,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{'),("let t=if let Some(t)=new{cold();t}else{","let t=if let (true,Some(t))=(has,new){cold();t}else{"),("validate(&st,hopt,fee,new,","validate(&st,hopt,fee,new,args.0.is_some(),")]
G['HB4']=[('new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{','new:Option<Pubkey>,has:bool,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{'),("let t=if let Some(t)=new{cold();t}else{","let t=if let (Some(t),true)=(new,has){cold();t}else{"),("validate(&st,hopt,fee,new,","validate(&st,hopt,fee,new,args.0.is_some(),")]

G['HB0']=[('new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{','new:Option<Pubkey>,has:bool,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{'),("let t=if let Some(t)=new{t}else{","let t=if let (true,Some(t))=(has,new){t}else{"),("validate(&st,hopt,fee,new,","validate(&st,hopt,fee,new,args.0.is_some(),")]

_HS=('new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{','new:Option<Pubkey>,has:bool,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{')
_HC=("validate(&st,hopt,fee,new,","validate(&st,hopt,fee,new,args.0.is_some(),")
G['G1']=[_HS,("let t=if let Some(t)=new{t}else{","let t=if has{new.unwrap_or_default()}else{"),_HC]
G['G2']=[_HS,("let t=if let Some(t)=new{t}else{","let t=if has{new.unwrap()}else{"),_HC]

_AM=("let cashback=!holder&&st.cashback;let args=&(new,);","let cashback=!holder&&st.cashback;")
G['P1']=[_AM,("{ let a=&ctx.accounts;","{ let a=&ctx.accounts;let args=&(new,);")]
G['P2']=[_AM,("holder_key=hk.0;","holder_key=hk.0;let args=&(new,);")]
G['P3']=[_AM,("fee_configurable:a.global.creator_fee_configurable};","fee_configurable:a.global.creator_fee_configurable};let args=&(new,);")]
import json
try:
  exec(open(os.path.dirname(os.path.abspath(__file__))+'/genes2.py').read())
except FileNotFoundError: pass
v=sys.argv[1]; d=f'{O}/var/{v}'
assert not os.path.exists(d), d+' exists'
subprocess.run(['rsync','-a',f'{O}/var/'+os.environ.get('MKV_BASE','m3')+'/',d+'/'],check=True)
p=d+'/src/creator/admin_cto.rs'; s=open(p).read()
for g in (sys.argv[2].split(',') if len(sys.argv)>2 and sys.argv[2] else []):
    for a,b in G[g]:
        assert s.count(a)==1,(g,a[:60]); s=s.replace(a,b)
open(p,'w').write(s)
print(v,'ok')
