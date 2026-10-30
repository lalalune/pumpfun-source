# fg2.py: w14a19 gene library on main f8dc901 (extends w14a08 fg.py; fixes anchors moved by #3241)
import fg
G=fg.G
QE='contains(&q)};let (holder,cashback,target,sharing_update,collect_old,skip)={'
G['RAR']=[(';let args=&(new,);let sk=a.sharing_config.key();',';let sk=a.sharing_config.key();'),(QE,'contains(&q)};let args=&(new,);let (holder,cashback,target,sharing_update,collect_old,skip)={')]
STB=fg.STB
G['B3']=[('let quote_locked={','let (cb0,hr0,my0)=(a.bonding_curve.is_cashback_coin,a.bonding_curve.is_holder_reward,a.bonding_curve.is_mayhem_mode);let quote_locked={'),(STB,'mayhem:my0,holder_reward:hr0,cashback:cb0')]
apply=fg.apply
import gen15
for _k in ('p1','p2','e3','tu8','hb0'): G[_k]=gen15.G[_k]
def apply(s,genes):
    n0=s.count('\n')
    for g in genes:
        ed=G[g](s) if callable(G[g]) else G[g]
        for a,b in ed:
            c=s.count(a)
            if c!=1: raise ValueError(f'{g}: anchor count {c}: {a[:70]}')
            s=s.replace(a,b)
    if s.count('\n')!=n0: raise ValueError('newline count changed')
    return s
G['s1']=gen15._s1
_HK=fg.HK
G['HKR']=[(_HK,'let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);let holder_key=&hk.0;')]
G['HKRv']=[(_HK,'let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);let holder_key=&hk.0;'),(',new,holder_key,&sk)?;',',new,*holder_key,&sk)?;')]
G['HKRv2']=[(_HK,'let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);let holder_key=&hk.0;'),(',new,holder_key,sk)?;',',new,*holder_key,sk)?;')]
G['HK1']=[(_HK,'let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);let holder_key=hk.0;')]
G['HK2']=[(_HK,'let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);let holder_key;holder_key=hk.0;')]
# TE: declare validate's result `target` early, between `let holder_key;` and `let hk=` (moves its 7 B SROA piece into hk's padding hole)
G['TE']=[('let holder_key;let hk=','let holder_key;let mut target;let hk='),('let mut target=validate(','target=validate(')]
G['TE2']=[('let holder_key;let hk=','let mut target;let holder_key;let hk='),('let mut target=validate(','target=validate(')]
G['TE3']=[('holder_key=hk.0;let quote_locked=','holder_key=hk.0;let mut target;let quote_locked='),('let mut target=validate(','target=validate(')]
_TV=('let mut target=validate(','target=validate(')
G['TE0']=[('->Result<()>{ let a=&ctx.accounts;let mint=','->Result<()>{ let mut target;let a=&ctx.accounts;let mint='),_TV]
G['TE0b']=[('let a=&ctx.accounts;let mint=a.mint.key();let shared=','let a=&ctx.accounts;let mint=a.mint.key();let mut target;let shared='),_TV]
G['TE4']=[('contains(&q)};let (holder,cashback,target,','contains(&q)};let mut target;let (holder,cashback,target,'),_TV]
G['TE5']=[('let (holder,cashback,target,sharing_update,collect_old,skip)={ let st=','let (holder,cashback,target,sharing_update,collect_old,skip)={ let mut target;let st='),_TV]
G['TE6']=[('let hopt=holder;let holder=hopt==Some(true);','let mut target;let hopt=holder;let holder=hopt==Some(true);'),_TV]
G['TE0']=[('let a=&ctx.accounts;let mint=a.mint.key();let shared=','let mut target;let a=&ctx.accounts;let mint=a.mint.key();let shared='),_TV]
G['TE6']=[('let hopt=hb;let holder=hb;','let mut target;let hopt=hb;let holder=hb;'),_TV]
