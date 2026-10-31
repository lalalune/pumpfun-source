# Joint long-spill-set spellings (w15a15): every late use of holder / cashback / fee reads a validate-exit value, as in
# the original (orig long spills: fee-tag phi [0x8e8], holder phi [0x950], cashback phi [0x958]; entry arg spills die in validate).
SIG=('->Result<Pubkey>{let holder=hopt==Some(true);','->Result<(Pubkey,bool,bool,Option<u64>)>{let holder=hopt==Some(true);')
FM0=('match fee{Some(f)=>{if st.quote_locked','let fee=match fee{Some(f)=>{if st.quote_locked')
FM1=('const u8)};}None=>{}}','const u8)};Some(f)}None=>None};')
FM1k=('const u8)};}None=>{}}','const u8)};}None=>{}};')
RET=('Ok(target)}pub fn execute','Ok((target,holder,cashback,fee))}pub fn execute')
CALL=('let cashback=!holder&&st.cashback;let args=&(new,);let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;',
      'let args=&(new,);let sk=a.sharing_config.key();let (mut target,holder,cashback,fee)=validate(&st,hopt,fee,new,&holder_key,&sk)?;')
TUP=('(holder,cashback,target,sharing_update,collect_old,skip)};','(holder,cashback,target,sharing_update,collect_old,skip,fee)};')
PAT=('let (_holder,cashback,target,sharing_update,collect_old,skip)={','let (_holder,cashback,target,sharing_update,collect_old,skip,fee)={')
HR=('curve.is_holder_reward=holder.unwrap_or(false);','curve.is_holder_reward=_holder;')
V={
 'j_all':[SIG,FM0,FM1,RET,CALL,TUP,PAT,HR],          # fee rebuilt per arm + holder + cashback from validate
 'j_nofee':[SIG,RET,CALL,TUP,PAT,HR],                # fee returned as is (tag = arg)
 'j_nohr':[SIG,FM0,FM1,RET,CALL,TUP,PAT],            # holder curve store keeps the arg
 'j_feeonly':[SIG,FM0,FM1,RET,CALL,TUP,PAT],         # placeholder, same as j_nohr but cashback kept from validate
}
