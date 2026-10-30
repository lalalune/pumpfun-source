def transform(s):
    a='let mut target=target; crate::trade_types::prepare_bonding_curve('
    assert s.count(a)==1
    s=s.replace(a,'post(&mut ctx,mint,holder_key,shared,holder,cashback,target,sharing_update,collect_old,fee)}#[inline(always)]fn post(ctx:&mut Context<AdminCto>,mint:Pubkey,holder_key:Pubkey,shared:bool,holder:bool,cashback:bool,target:Pubkey,sharing_update:Option<Option<Pubkey>>,collect_old:bool,fee:Option<u64>)->Result<()>{let a=&ctx.accounts;let mut target=target; crate::trade_types::prepare_bonding_curve(')
    b='pub fn execute(ctx:Context<AdminCto>,'
    assert s.count(b)==1
    s=s.replace(b,'pub fn execute(mut ctx:Context<AdminCto>,')
    return s
