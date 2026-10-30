# fg.py: gene library for w14a08 (main 308b545 source anchors). G[name] = [(old,new),...]
import json
SIG='new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{'
HARM='CtoNewCreatorNotAllowed));}*holder_key}else{'
CMP='if t==*sharing||t==*holder_key{'
VAL='let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;'
HK='let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;'
HK0='let (holder_key,_)=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);'
QL='let quote_locked={let q=a.bonding_curve.quote_mint;q==Pubkey::default()||q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(&q)};'
STB='mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin'
L289="if st.holder_reward&&!(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}"
G={
 'RAR':[(';let args=&(new,);let sk=a.sharing_config.key();',';let sk=a.sharing_config.key();'),('let (holder,cashback,target,sharing_update,collect_old,skip)={ let st=','let args=&(new,);let (holder,cashback,target,sharing_update,collect_old,skip)={ let st=')],
 'N289':[(L289,"if st.holder_reward{if !holder{return Err(error!(PumpError::HolderRewardCreatorImmutable));}}")],
 'V2':[(SIG,'new:Option<Pubkey>,holder_key:Pubkey,sharing:Pubkey)->Result<Pubkey>{'),(HARM,'CtoNewCreatorNotAllowed));}holder_key}else{'),(CMP,'if t==sharing||t==holder_key{'),(VAL,'let mut target=validate(&st,hopt,fee,args.0,holder_key,sk)?;')],
 'V2N':[(SIG,'new:Option<Pubkey>,holder_key:Pubkey,sharing:Pubkey)->Result<Pubkey>{'),(HARM,'CtoNewCreatorNotAllowed));}holder_key}else{'),(CMP,'if t==sharing||t==holder_key{'),(VAL,'let mut target=validate(&st,hopt,fee,new,holder_key,sk)?;')],
 'V1':[(SIG,'new:Option<Pubkey>,holder_key:Pubkey,sharing:&Pubkey)->Result<Pubkey>{'),(HARM,'CtoNewCreatorNotAllowed));}holder_key}else{'),(CMP,'if t==*sharing||t==holder_key{'),(VAL,'let mut target=validate(&st,hopt,fee,new,holder_key,&sk)?;')],
 'VS':[(SIG,'new:Option<Pubkey>,holder_key:&Pubkey,sharing:Pubkey)->Result<Pubkey>{'),(CMP,'if t==sharing||t==*holder_key{'),(VAL,'let mut target=validate(&st,hopt,fee,new,&holder_key,sk)?;')],
 'VA':[(VAL,'let mut target=validate(&st,hopt,fee,args.0,&holder_key,&sk)?;')],
 'HK0':[(HK,HK0)],
 'B3':[(QL,'let (cb0,hr0,my0)=(a.bonding_curve.is_cashback_coin,a.bonding_curve.is_holder_reward,a.bonding_curve.is_mayhem_mode);'+QL),(STB,'mayhem:my0,holder_reward:hr0,cashback:cb0')],
 'QLIN':[(QL,''),('cashback:a.bonding_curve.is_cashback_coin,quote_locked,','cashback:a.bonding_curve.is_cashback_coin,quote_locked:crate::pump_quote::global_quote(a.bonding_curve.quote_mint,&a.global),')],
}
K=json.load(open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/sizeknobs-cto.json'))['knobs']
for k in K:
    ed=k.get('edit') or k.get('edits') or []
    if ed: G['K:'+k['name']]=[(e['old'],e['new']) for e in ed]
def apply(s,genes):
    n0=s.count('\n')
    for g in genes:
        for a,b in (G[g](s) if callable(G[g]) else G[g]):
            c=s.count(a)
            if c!=1: raise ValueError(f'{g}: anchor count {c}: {a[:70]}')
            s=s.replace(a,b)
    if s.count('\n')!=n0: raise ValueError('newline count changed')
    return s
SH='let shared=a.sharing_config.key()==a.bonding_curve.creator&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();'
G['PDA']=[(SH+HK,HK+SH)]
G['PDA0']=[(SH+HK,HK0+SH)]
_A=';let args=&(new,);let sk=a.sharing_config.key();'
G['ARGstart']=[(_A,';let sk=a.sharing_config.key();'),('{ let a=&ctx.accounts;let mint=a.mint.key();','{ let args=&(new,);let a=&ctx.accounts;let mint=a.mint.key();')]
G['ARGpq']=[(_A,';let sk=a.sharing_config.key();'),(QL,'let args=&(new,);'+QL)]
G['ARGsh']=[(_A,';let sk=a.sharing_config.key();'),('let a=&ctx.accounts;let mint=a.mint.key();let shared=','let a=&ctx.accounts;let mint=a.mint.key();let args=&(new,);let shared=')]
G['ARGhopt']=[(_A,';let sk=a.sharing_config.key();'),('fee_configurable:a.global.creator_fee_configurable};let hopt=holder;','fee_configurable:a.global.creator_fee_configurable};let args=&(new,);let hopt=holder;')]
G['ARGsk']=[(_A,';let sk=a.sharing_config.key();let args=&(new,);')]
G['ARGst']=[(_A,';let sk=a.sharing_config.key();'),('let (holder,cashback,target,sharing_update,collect_old,skip)={ let st=','let (holder,cashback,target,sharing_update,collect_old,skip)={ let args=&(new,);let st=')]

exec(open(__file__.replace('fg.py','gen15.py')).read().replace("G['rar']","_rar").replace("G['hb0']","G['HB0']"))
G['V1H']=[('new:Option<Pubkey>,has:bool,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{','new:Option<Pubkey>,has:bool,holder_key:Pubkey,sharing:&Pubkey)->Result<Pubkey>{'),(HARM,'CtoNewCreatorNotAllowed));}holder_key}else{'),(CMP,'if t==*sharing||t==holder_key{'),('validate(&st,hopt,fee,new,args.0.is_some(),&holder_key,&sk)?;','validate(&st,hopt,fee,new,args.0.is_some(),holder_key,&sk)?;')]
QLc='let quote_locked=crate::pump_quote::global_quote(a.bonding_curve.quote_mint,&a.global);'
G['B3c']=[(QLc,'let (cb0,hr0,my0)=(a.bonding_curve.is_cashback_coin,a.bonding_curve.is_holder_reward,a.bonding_curve.is_mayhem_mode);'+QLc),(STB,'mayhem:my0,holder_reward:hr0,cashback:cb0')]
G['QLINc']=[(QLc,''),('cashback:a.bonding_curve.is_cashback_coin,quote_locked,','cashback:a.bonding_curve.is_cashback_coin,quote_locked:crate::pump_quote::global_quote(a.bonding_curve.quote_mint,&a.global),')]
G['HV1']=[('if st.holder_reward&&!(hopt==Some(true)){','if st.holder_reward&&!holder{')]
G['HV2']=[('->Result<Pubkey>{let holder=hopt==Some(true);\n if st.mayhem{return Err(error!(PumpError::CtoNotAllowedForMayhemCoin));}','->Result<Pubkey>{\n if st.mayhem{return Err(error!(PumpError::CtoNotAllowedForMayhemCoin));}let holder=hopt==Some(true);')]
G['HV3']=[('->Result<Pubkey>{let holder=hopt==Some(true);','->Result<Pubkey>{let holder=matches!(hopt,Some(true));')]
_SK=';let args=&(new,);let sk=a.sharing_config.key();let mut target='
G['SK1']=[(_SK,';let args=&(new,);let mut target='),('let shared=a.sharing_config.key()==a.bonding_curve.creator&&','let sk=a.sharing_config.key();let shared=sk==a.bonding_curve.creator&&')]
G['SK2']=[(_SK,';let args=&(new,);let mut target='),('let holder_key;let hk=','let sk=a.sharing_config.key();let holder_key;let hk=')]
G['SK3']=[(_SK,';let args=&(new,);let mut target='),('let (holder,cashback,target,sharing_update,collect_old,skip)={ let st=','let sk=a.sharing_config.key();let (holder,cashback,target,sharing_update,collect_old,skip)={ let st=')]
