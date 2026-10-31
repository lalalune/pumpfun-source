#!/usr/bin/env python3
"""hb.py <src> <name|all>: write src_edits/<name>.py for helper-boundary genes (EDITS list of (old,new)); '+'-joined names compose."""
import sys,os,json
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a58-cto-tafterlevy')
src=open(sys.argv[1]).read()
G={}
# ---------- (1) finish: curve update + pool CPI tail as a nested fn
T1_OLD=''' let (old_creator,old_fee)={
  let curve=&mut ctx.accounts.bonding_curve;'''
POOLTAIL='''}else{msg!("No canonical pump pool for this mint; curve only");}
 let e=AdminCtoEvent{'''
G['f1']=[(T1_OLD,''' let (old_creator,old_fee,nf,pool_updated)=finish(&ctx,target,holder,cashback,fee,signer_seeds)?;fn finish(ctx:&Context<AdminCto>,target:Pubkey,holder:bool,cashback:bool,fee:Option<u64>,signer_seeds:&[&[&[u8]]])->Result<(Pubkey,u64,u64,bool)>{let (old_creator,old_fee)={
  let curve=&mut ctx.accounts.bonding_curve.clone();'''),]
# f1 uses &mut via accounts: need &mut ctx; rewrite properly below
G['f1']=[(T1_OLD,''' let (old_creator,old_fee,nf,pool_updated)=finish(&mut ctx,target,holder,cashback,fee,signer_seeds)?;fn finish(ctx:&mut Context<AdminCto>,target:Pubkey,holder:bool,cashback:bool,fee:Option<u64>,signer_seeds:&[&[&[u8]]])->Result<(Pubkey,u64,u64,bool)>{let (old_creator,old_fee)={
  let curve=&mut ctx.accounts.bonding_curve;'''),
 (POOLTAIL,'''}else{msg!("No canonical pump pool for this mint; curve only");}Ok((old_creator,old_fee,nf,pool_updated))}let a=&ctx.accounts;
 let e=AdminCtoEvent{'''),
 ('pub fn execute(ctx:Context<AdminCto>','pub fn execute(mut ctx:Context<AdminCto>')]
# f1c: same tail as an immediately-called closure
G['f1c']=[(T1_OLD,''' let (old_creator,old_fee,nf,pool_updated)=(||->Result<(Pubkey,u64,u64,bool)>{let (old_creator,old_fee)={
  let curve=&mut ctx.accounts.bonding_curve;'''),
 (POOLTAIL,'''}else{msg!("No canonical pump pool for this mint; curve only");}Ok((old_creator,old_fee,nf,pool_updated))})()?;let a=&ctx.accounts;
 let e=AdminCtoEvent{''')]
# f1a: finish takes the accounts struct
G['f1a']=[(T1_OLD,''' let (old_creator,old_fee,nf,pool_updated)=finish(ctx.accounts,target,holder,cashback,fee,signer_seeds)?;fn finish(a:&mut AdminCto,target:Pubkey,holder:bool,cashback:bool,fee:Option<u64>,signer_seeds:&[&[&[u8]]])->Result<(Pubkey,u64,u64,bool)>{let (old_creator,old_fee)={
  let curve=&mut a.bonding_curve;'''),
 (''' (old_creator,old_fee)};
 let a=&ctx.accounts;''',''' (old_creator,old_fee)};
 let a=&*a;'''),
 (POOLTAIL,'''}else{msg!("No canonical pump pool for this mint; curve only");}Ok((old_creator,old_fee,nf,pool_updated))}let a=&ctx.accounts;
 let e=AdminCtoEvent{''')]
# ---------- (2) pool CPI alone
P_OLD=''' if pool_updated{


  crate::pump_amm::cpi::admin_cto_pool('''
P_END='''signer_seeds),pargs.0,pargs.1,pargs.2)?;
 }else{'''
G['p2']=[(P_OLD,''' if pool_updated{


  pool(&ctx,pargs,signer_seeds)?;fn pool(ctx:&Context<AdminCto>,pargs:(Pubkey,bool,Option<u64>),signer_seeds:&[&[&[u8]]])->Result<()>{let a=&ctx.accounts;crate::pump_amm::cpi::admin_cto_pool('''),
 (P_END,'''signer_seeds),pargs.0,pargs.1,pargs.2)}
 }else{''')]
G['p2a']=[(P_OLD,''' if pool_updated{


  pool(a,pargs,signer_seeds)?;fn pool(a:&AdminCto,pargs:(Pubkey,bool,Option<u64>),signer_seeds:&[&[&[u8]]])->Result<()>{crate::pump_amm::cpi::admin_cto_pool('''),
 (P_END,'''signer_seeds),pargs.0,pargs.1,pargs.2)}
 }else{''')]
# p2b: pool helper owns the if/else (gate inside)
G['p2b']=[(P_OLD,''' pool(&ctx,pool_updated,pargs,signer_seeds)?;fn pool(ctx:&Context<AdminCto>,pool_updated:bool,pargs:(Pubkey,bool,Option<u64>),signer_seeds:&[&[&[u8]]])->Result<()>{let a=&ctx.accounts;if pool_updated{


  crate::pump_amm::cpi::admin_cto_pool('''),
 (POOLTAIL,'''}else{msg!("No canonical pump pool for this mint; curve only");}Ok(())}
 let e=AdminCtoEvent{''')]
# ---------- (3) event build + emit
E_OLD=''' let e=AdminCtoEvent{timestamp:Clock::get()?.unix_timestamp,authority:a.admin_set_creator_authority.key(),mint,bonding_curve:a.bonding_curve.key(),old_creator,new_creator:a.bonding_curve.creator,is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback_coin:a.bonding_curve.is_cashback_coin,old_creator_fee_bps:old_fee,new_creator_fee_bps:nf,sharing_config_reset:sharing_update.is_some(),swept_to_holder_vault:swept,pool_updated};emit!(e);emit_cpi!(e);Ok(())'''
EV_BODY='''let a=&ctx.accounts;let e=AdminCtoEvent{timestamp:Clock::get()?.unix_timestamp,authority:a.admin_set_creator_authority.key(),mint,bonding_curve:a.bonding_curve.key(),old_creator,new_creator:a.bonding_curve.creator,is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback_coin:a.bonding_curve.is_cashback_coin,old_creator_fee_bps:old_fee,new_creator_fee_bps:nf,sharing_config_reset,swept_to_holder_vault:swept,pool_updated};emit!(e);emit_cpi!(e);Ok(())'''
G['e3']=[(E_OLD,''' event(&ctx,mint,old_creator,old_fee,nf,sharing_update.is_some(),swept,pool_updated)}fn event(ctx:&Context<AdminCto>,mint:Pubkey,old_creator:Pubkey,old_fee:u64,nf:u64,sharing_config_reset:bool,swept:u64,pool_updated:bool)->Result<()>{'''+EV_BODY)]
G['e3q']=[(E_OLD,''' event(&ctx,mint,old_creator,old_fee,nf,sharing_update.is_some(),swept,pool_updated)?;Ok(())}fn event(ctx:&Context<AdminCto>,mint:Pubkey,old_creator:Pubkey,old_fee:u64,nf:u64,sharing_config_reset:bool,swept:u64,pool_updated:bool)->Result<()>{'''+EV_BODY)]
# e3b: build event in a helper returning the struct, emit in execute
G['e3b']=[(E_OLD,''' let e=event(a,mint,old_creator,old_fee,nf,sharing_update.is_some(),swept,pool_updated)?;fn event(a:&AdminCto,mint:Pubkey,old_creator:Pubkey,old_fee:u64,nf:u64,sharing_config_reset:bool,swept:u64,pool_updated:bool)->Result<AdminCtoEvent>{Ok(AdminCtoEvent{timestamp:Clock::get()?.unix_timestamp,authority:a.admin_set_creator_authority.key(),mint,bonding_curve:a.bonding_curve.key(),old_creator,new_creator:a.bonding_curve.creator,is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback_coin:a.bonding_curve.is_cashback_coin,old_creator_fee_bps:old_fee,new_creator_fee_bps:nf,sharing_config_reset,swept_to_holder_vault:swept,pool_updated})}emit!(e);emit_cpi!(e);Ok(())''')]
# ---------- (8) CtoState literal in fn state
S_OLD='''let st=CtoState{creator:a.bonding_curve.creator,max_fee:a.global.max_configurable_creator_fee_bps,mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin,quote_locked,holder_enabled:a.global.is_holder_reward_enabled,fee_configurable:a.global.creator_fee_configurable};'''
S_LIT='''CtoState{creator:a.bonding_curve.creator,max_fee:a.global.max_configurable_creator_fee_bps,mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin,quote_locked,holder_enabled:a.global.is_holder_reward_enabled,fee_configurable:a.global.creator_fee_configurable}'''
G['s8']=[(S_OLD,'let st=state(a,quote_locked);fn state(a:&AdminCto,quote_locked:bool)->CtoState{'+S_LIT+'}')]
G['s8c']=[(S_OLD,'let st=state(&ctx,quote_locked);fn state(ctx:&Context<AdminCto>,quote_locked:bool)->CtoState{let a=&ctx.accounts;'+S_LIT+'}')]
# ---------- (6) token_frozen / token_raw_amount by hand
def TF(x): return '{let x:&AccountInfo='+x+';if x.data_is_empty(){false}else{let d=x.try_borrow_data()?;let t=anchor_spl::token_interface::TokenAccount::try_deserialize(&mut &d[..])?;t.is_frozen()}}'
def TR(x): return '{let x:&AccountInfo='+x+';if x.data_is_empty(){0}else{let d=x.try_borrow_data()?;let t=anchor_spl::token_interface::TokenAccount::try_deserialize(&mut &d[..])?;t.amount}}'
W1='if token_frozen(a.current_creator_quote_token_account.as_ref())?{'
W2='&&!token_frozen(a.creator_vault_quote_token_account.as_ref())?);'
W3='let do_coin=coin_present&&!token_frozen(a.coin_creator_vault_ata.as_ref())?;'
S1='let amm_frozen=!a.coin_creator_vault_ata.data_is_empty()&&token_frozen(a.coin_creator_vault_ata.as_ref())?;'
S2='require!(token_raw_amount(a.coin_creator_vault_ata.as_ref())?==0,'
S3='let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;'
G['t6w1']=[(W1,'if '+TF('a.current_creator_quote_token_account.as_ref()')+'{')]
G['t6w2']=[(W2,'&&!'+TF('a.creator_vault_quote_token_account.as_ref()')+');')]
G['t6w3']=[(W3,'let do_coin=coin_present&&!'+TF('a.coin_creator_vault_ata.as_ref()')+';')]
G['t6s1']=[(S1,'let amm_frozen=!a.coin_creator_vault_ata.data_is_empty()&&'+TF('a.coin_creator_vault_ata.as_ref()')+';')]
G['t6s2']=[(S2,'require!('+TR('a.coin_creator_vault_ata.as_ref()')+'==0,')]
G['t6s3']=[(S3,'let amount='+TR('a.creator_vault_quote_token_account.as_ref()')+';let frozen='+TF('a.creator_vault_quote_token_account.as_ref()')+';')]
G['t6w']=G['t6w1']+G['t6w2']+G['t6w3']
G['t6s']=G['t6s1']+G['t6s2']+G['t6s3']
G['t6']=G['t6w']+G['t6s']
# ---------- (5) sweep arms as nested fns
SW_N='''  if native{let rent=Rent::get()?;let min=rent.minimum_balance(0);let amount=a.creator_vault.lamports().saturating_sub(min);
   if amount>0{crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner).map(|()|amount)}else{Ok(amount)}}else{let amount=token_raw_amount'''
G['w5n']=[(SW_N,'''  if native{native_arm(a,&vsigner)}fn native_arm(a:&AdminCto,vsigner:&[&[&[u8]]])->Result<u64>{let rent=Rent::get()?;let min=rent.minimum_balance(0);let amount=a.creator_vault.lamports().saturating_sub(min);
   if amount>0{crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,vsigner).map(|()|amount)}else{Ok(amount)}}if native{unreachable!()}else{let amount=token_raw_amount''')]
# simpler w5n: keep if/else structure: if native{native_arm(..)}else{...}
G['w5n']=[(SW_N,'''  if native{native_arm(a,&vsigner)}else{let amount=token_raw_amount''')]
NATIVE_FN='''fn native_arm(a:&AdminCto,vsigner:&[&[&[u8]]])->Result<u64>{let rent=Rent::get()?;let min=rent.minimum_balance(0);let amount=a.creator_vault.lamports().saturating_sub(min);if amount>0{crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,vsigner).map(|()|amount)}else{Ok(amount)}}'''
G['w5n'].append(('fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{',NATIVE_FN+'fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{'))
# fix newline: SW_N contains 1 newline; replacement has 0 -> add one
G['w5n'][0]=(SW_N,'''  if native{native_arm(a,&vsigner)}else{
let amount=token_raw_amount''')
TOK_START='''else{let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;'''
TOK_END='''a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),amount,&vsigner)?;}
   Ok(amount)}'''
G['w5t']=[(TOK_START,'''else{token_arm(a,&vsigner)}fn token_arm(a:&AdminCto,vsigner:&[&[&[u8]]])->Result<u64>{let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;'''),
 (TOK_END,'''a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),amount,vsigner)?;}
   Ok(amount)}''')]
# ---------- (4) wallet: collect part as separate fn
WG='''if token_frozen(a.current_creator_quote_token_account.as_ref())?{msg!("Creator quote token account is frozen; fees left in the vaults");}else{
  let collection_native'''
WE=''' }}Ok(())}
 let swept;'''
G['w4c']=[(WG,'''if token_frozen(a.current_creator_quote_token_account.as_ref())?{msg!("Creator quote token account is frozen; fees left in the vaults");}else{collect(ctx)?;}}Ok(())}fn collect(ctx:&Context<AdminCto>)->Result<()>{let a=&ctx.accounts;{
  let collection_native'''),
 (WE,''' }Ok(())}
 let swept;''')]
for k in list(G):
    pass
def build(spec):
    E=[]
    for g in spec.split('+'): E+=G[g]
    s=src; n0=s.count('\n')
    for a,b in E:
        c=s.count(a); assert c==1,(spec,c,a[:100]); s=s.replace(a,b)
    assert s.count('\n')==n0,(spec,s.count('\n')-n0)
    return E
# ---------- (4b) wallet written by hand into execute's if collect_old
G['w4i']=[('if collect_old{wallet(&ctx)?;}fn wallet(ctx:&Context<AdminCto>)->Result<()>{let a=&ctx.accounts;','if collect_old{let a=&ctx.accounts;'),(WE,''' }}}
 let swept;''')]
G['w4ir']=[('if collect_old{wallet(&ctx)?;}fn wallet(ctx:&Context<AdminCto>)->Result<()>{let a=&ctx.accounts;','if collect_old{let ctx=&ctx;let a=&ctx.accounts;'),(WE,''' }}}
 let swept;''')]
# ---------- (7) validate body into execute's state block
VL='fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);'
import re as _re
_i=src.index(VL); _j=src.index(' Ok(target)}pub fn execute(')
VBODY=src[_i+len(VL):_j]
EX_LINE_START=' Ok(target)}pub fn execute('
_k=src.index('let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;')
EX_HEAD=src[_j+len(' Ok(target)}'):_k]  # 'pub fn execute(...)...let sk=a.sharing_config.key();'
def v7(kind):
    if kind=='c':
        open_='let mut target=(||->Result<Pubkey>{let st=&st;let holder_key=&holder_key;let sharing=&sk;let holder=hopt==Some(true);'
        body=VBODY; close=' Ok(target)})()?;'
    elif kind=='l':
        open_="let mut target=('v:{let st=&st;let holder_key=&holder_key;let sharing=&sk;let holder=hopt==Some(true);"
        body=VBODY.replace('return Err(','break \'v Err('); close=' Ok(target)})?;'
    elif kind=='m':
        open_="let mut target=match 'v:{let st=&st;let holder_key=&holder_key;let sharing=&sk;let holder=hopt==Some(true);"
        body=VBODY.replace('return Err(','break \'v Err('); close=' Ok(target)}{Ok(t)=>t,Err(e)=>return Err(e)};'
    new_line1=EX_HEAD+open_
    # whole span from VL to end of validate call
    old=src[_i:_k+len('let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;')]
    new=new_line1+body+close
    return [(old,new)]
G['v7c']=v7('c'); G['v7l']=v7('l'); G['v7m']=v7('m')
G['w5t']=[(TOK_START,'''else{fn token_arm(a:&AdminCto,vsigner:&[&[&[u8]]])->Result<u64>{let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;'''),
 (TOK_END,'''a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),amount,vsigner)?;}
   Ok(amount)}token_arm(a,&vsigner)}''')]
G['w5']=G['w5n']+G['w5t']
# curve update as a call-free helper
CU_OLD=''' let (old_creator,old_fee)={
  let curve=&mut ctx.accounts.bonding_curve;let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;'''
CU_END=''' (old_creator,old_fee)};
 let a=&ctx.accounts;'''
G['c1']=[(CU_OLD,''' let (old_creator,old_fee)=update(&mut ctx.accounts.bonding_curve,target,cashback,holder,fee);fn update(curve:&mut BondingCurve,target:Pubkey,cashback:bool,holder:bool,fee:Option<u64>)->(Pubkey,u64){
  let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;'''),(CU_END,''' (old_creator,old_fee)}
 let a=&ctx.accounts;''')]
G['c1b']=[(CU_OLD,''' let (old_creator,old_fee)=update(&mut ctx.accounts.bonding_curve,target,cashback,holder,fee);fn update(curve:&mut Box<Account<BondingCurve>>,target:Pubkey,cashback:bool,holder:bool,fee:Option<u64>)->(Pubkey,u64){
  let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;'''),(CU_END,''' (old_creator,old_fee)}
 let a=&ctx.accounts;''')]
# pool gate helper
PU='let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;'
G['pu']=[(PU,'let pool_updated=pool_ok(&a.pool);fn pool_ok(p:&AccountInfo)->bool{!p.data_is_empty() && p.owner==&AMM}')]
# shared gate helper
SH='let shared=a.sharing_config.key()==a.bonding_curve.creator&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();'
G['sh']=[(SH,'let shared=is_shared(a);fn is_shared(a:&AdminCto)->bool{a.sharing_config.key()==a.bonding_curve.creator&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty()}')]
G['sh2']=[(SH,'let shared=is_shared(&a.sharing_config,&a.bonding_curve.creator);fn is_shared(s:&AccountInfo,c:&Pubkey)->bool{s.key()==*c&&s.owner==&FEES&&!s.data_is_empty()}')]
# holder-rewards PDA helper
HK='let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;'
G['hk']=[(HK,'let holder_key;let hk=holder_pda(&mint);fn holder_pda(mint:&Pubkey)->(Pubkey,u8){Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID)}holder_key=hk.0;')]
# sweep dest PDA helper
SD='let dest=Pubkey::find_program_address(&[b"creator-vault",holder_key.as_ref()],&crate::ID).0;'
G['sd']=[(SD,'let dest=vault_pda(holder_key);fn vault_pda(k:&Pubkey)->Pubkey{Pubkey::find_program_address(&[b"creator-vault",k.as_ref()],&crate::ID).0}')]
# sharing decision tuple as helper (call-free)
SD2='let (collect_old,sharing_update,skip)=if shared{if holder{(false,Some(None),false)}else{target=st.creator;(false,Some(args.0),true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};'
G['dz']=[(SD2,'let (collect_old,sharing_update,skip)=decide(&st,shared,holder,&mut target,args.0);fn decide(st:&CtoState,shared:bool,holder:bool,target:&mut Pubkey,n:Option<Pubkey>)->(bool,Option<Option<Pubkey>>,bool){if shared{if holder{(false,Some(None),false)}else{*target=st.creator;(false,Some(n),true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)}}')]
def v7x(open_,close,body=None,head=None):
    old=src[_i:_k+len('let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;')]
    return [(old,(head if head is not None else EX_HEAD)+open_+(body if body is not None else VBODY)+close)]
C0=' Ok(target)})()?;'
G['v7c2']=v7x('let mut target=(||->Result<Pubkey>{let holder_key=&holder_key;let sharing=&sk;let holder=hopt==Some(true);',C0)
G['v7cB']=v7x('let (stp,hkp,skp)=(&st,&holder_key,&sk);let mut target=(move||->Result<Pubkey>{let st=stp;let holder_key=hkp;let sharing=skp;let holder=hopt==Some(true);',C0)
G['v7cR']=v7x('let mut target=(|st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey|->Result<Pubkey>{let holder=hopt==Some(true);',' Ok(target)})(&st,hopt,fee,new,&holder_key,&sk)?;')
G['v7cH']=v7x('let mut target=(||->Result<Pubkey>{let st=&st;let holder_key=&holder_key;let sharing=&sk;',C0)
G['v7cV']=v7x('let v=||->Result<Pubkey>{let st=&st;let holder_key=&holder_key;let sharing=&sk;let holder=hopt==Some(true);',' Ok(target)};let mut target=v()?;')
G['v7cK']=v7x('let mut target=(||->Result<Pubkey>{let st=&st;let holder_key=&holder_key;let sharing=&sk;let holder=hopt==Some(true);',C0,body=VBODY.replace(' let cashback=if holder{false}else{st.cashback};',' let cashback=cashback;'))
G['v7cM']=v7x('let (stp,hkp,skp)=(&st,&holder_key,&sk);let mut target=(move||->Result<Pubkey>{let (st,holder_key,sharing)=(stp,hkp,skp);let holder=hopt==Some(true);',C0)
TN='crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner).map(|()|amount)}else{Ok(amount)}}'
TC='crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner)'
G['n1']=[(TN,TC+'?;Ok(amount)}else{Ok(amount)}}')]
G['n2']=[(TN,'match '+TC+'{Ok(())=>Ok(amount),Err(e)=>Err(e)}}else{Ok(amount)}}')]
G['n4']=[(TN,TC+'.and(Ok(amount))}else{Ok(amount)}}')]
G['n5']=[(TN,'if let Err(e)='+TC+'{return Err(e);}Ok(amount)}else{Ok(amount)}}')]
G['n6']=[('   if amount>0{crate::legacy_buy::native_payments::ensure_rent_exempt',' if amount>0{crate::legacy_buy::native_payments::ensure_rent_exempt'),(TN,TC+'?;}Ok(amount)}')]
G['n7']=[(TN,TC+'.map(|_|amount)}else{Ok(amount)}}')]
G['n8']=[(TN,TC+'.map(|()|amount)}else{Ok(0)}}')]
G['wc']=[('if collect_old{wallet(&ctx)?;}fn wallet(ctx:&Context<AdminCto>)->Result<()>{let a=&ctx.accounts;','if collect_old{(||->Result<()>{let a=&ctx.accounts;'),(WE,''' }}Ok(())})()?;}
 let swept;''')]
G['wcr']=[('if collect_old{wallet(&ctx)?;}fn wallet(ctx:&Context<AdminCto>)->Result<()>{let a=&ctx.accounts;','if collect_old{(||->Result<()>{let ctx=&ctx;let a=&ctx.accounts;'),(WE,''' }}Ok(())})()?;}
 let swept;''')]
SWH='swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{let a=&ctx.accounts;'
SWE='   Ok(amount)}\n\n\n\n\n\n }\n\n'
G['swc']=[(SWH,'swept=(!skip).then(||->Result<u64>{let ctx=&ctx;let holder_key=&holder_key;let a=&ctx.accounts;'),(SWE,'   Ok(amount)}\n\n\n\n\n\n }).transpose()?.unwrap_or(0);\n\n')]
G['swc2']=[(SWH,'swept=(!skip).then(||->Result<u64>{let a=&ctx.accounts;let holder_key=&holder_key;'),(SWE,'   Ok(amount)}\n\n\n\n\n\n }).transpose()?.unwrap_or(0);\n\n')]
if __name__=='__main__':
    names=list(G) if sys.argv[2]=='all' else sys.argv[2:]
    for n in names:
        E=build(n); open(f'{O}/src_edits/{n}.py','w').write('EDITS='+repr(E)+'\n'); print('ok',n)
G['v7f']=[('fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);','fn validate(st:&CtoState,hopt:&Option<bool>,fee:&Option<u64>,new:&Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder=*hopt==Some(true);'),
 (' if st.holder_reward&&!(hopt==Some(true)){',' if st.holder_reward&&!(*hopt==Some(true)){'),
 ('  let t=if let Some(t)=new{t}else{','  let t=if let Some(t)=*new{t}else{'),
 (' match fee{Some(f)=>{if st.quote_locked{',' match *fee{Some(f)=>{if st.quote_locked{'),
 ('let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;','let mut target=validate(&st,&hopt,&fee,&new,&holder_key,&sk)?;')]
SWC='swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);'
G['sg1']=[(SWC,'swept=(!skip).then(||sweep(&ctx,&holder_key)).unwrap_or(Ok(0))?;')]
G['sg2']=[(SWC,'swept=match (!skip).then(||sweep(&ctx,&holder_key)){Some(r)=>r?,None=>0};')]
G['sg3']=[(SWC,'swept=if skip{0}else{sweep(&ctx,&holder_key)?};')]
G['sg4']=[(SWC,'swept=(!skip).then(||sweep(&ctx,&holder_key)).unwrap_or(Ok(0)).map_err(|e|e)?;')]
G['sg5']=[(SWC,'swept=if !skip{sweep(&ctx,&holder_key)}else{Ok(0)}?;')]
G['r1']=[('   if amount>0{crate::legacy_buy','   return if amount>0{crate::legacy_buy'),
 ('.map(|()|amount)}else{Ok(amount)}}else{let amount=token_raw_amount','.map(|()|amount)}else{Ok(amount)};}let amount=token_raw_amount'),
 ('   Ok(amount)}\n\n\n\n\n\n }\n\n','   Ok(amount)\n\n\n\n\n\n }\n\n')]
_VS='fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{'
_VC='let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;'
_ARM=' let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{'
G['fv1']=[(_VS,_VS.replace('new:Option<Pubkey>','new:&&Option<Pubkey>')),('  let t=if let Some(t)=new{t}else{','  let t=if let Some(t)=**new{t}else{'),(_VC,_VC.replace(',new,',',&&new,'))]
G['fv1y']=[(_VS,_VS.replace('new:Option<Pubkey>','new:&&Option<Pubkey>')),(_ARM,_ARM+'let new=**new;'),(_VC,_VC.replace(',new,',',&&new,'))]
G['fv2']=[(_VS,_VS.replace('new:Option<Pubkey>','new:&Option<Pubkey>')),('  let t=if let Some(t)=new{t}else{','  let t=if let Some(t)=*new{t}else{'),(_VC,_VC.replace(',new,',',&new,'))]
G['fv2y']=[(_VS,_VS.replace('new:Option<Pubkey>','new:&Option<Pubkey>')),(_ARM,_ARM+'let new=*new;'),(_VC,_VC.replace(',new,',',&new,'))]
_old7=src[_i:_k+len('let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;')]
G['v7h']=[(_old7,EX_HEAD+'let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;'+VL+VBODY+' Ok(target)}')]
# w14a42 tafterlevy genes (vy1 copy, 306 let-else) applied on top of v7c
G['ny']=[('*holder_key}else{\n','*holder_key}else{let new=new;\n')]
G['le']=[('  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};','  let Some(t)=new else{return Err(error!(PumpError::CtoNewCreatorRequired));};')]
_L306='  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};'
_ER='return Err(error!(PumpError::CtoNewCreatorRequired));'
G['z_blk']=[(_L306,'  let Some(t)={new} else{'+_ER+'};')]
G['z_der']=[(_L306,'  let Some(t)=*&new else{'+_ER+'};')]
G['z_cl']=[(_L306,'  let Some(t)=new.clone() else{'+_ER+'};')]
G['z_ref']=[(_L306,'  let Some(&t)=new.as_ref() else{'+_ER+'};')]
G['z_m']=[(_L306,'  let t=match new{Some(t)=>t,None=>{'+_ER+'}};')]
G['z_m2']=[(_L306,'  let t=match new{None=>{'+_ER+'},Some(t)=>t};')]
G['z_ok']=[(_L306,'  let t=new.ok_or_else(||error!(PumpError::CtoNewCreatorRequired))?;')]
G['z_ny']=[(_L306,'  let new=new;let Some(t)=new else{'+_ER+'};')]
G['ny_h']=[(' let target=if holder{if new.is_some()',' let target=if holder{let new=new;if new.is_some()')]
G['ny_t']=[(' let target=if holder{if new.is_some()',' let new=new;let target=if holder{if new.is_some()')]
G['ny_c']=[('let sharing=&sk;let holder=hopt==Some(true);','let sharing=&sk;let holder=hopt==Some(true);let new=new;')]
G['ny_r']=[('*holder_key}else{\n','*holder_key}else{let new=&new;\n'),(_L306,'  let Some(t)=*new else{'+_ER+'};')]
G['sh_iflet']=[(" match sharing_update{Some(val)=>{\n"," if let Some(val)=sharing_update{{\n"),("signer_seeds),val)?;\n\n }None=>{}}\n","signer_seeds),val)?;\n\n }}\n")]
G['sh_none1']=[(" match sharing_update{Some(val)=>{\n"," match sharing_update{None=>{}Some(val)=>{\n"),("signer_seeds),val)?;\n\n }None=>{}}\n","signer_seeds),val)?;\n\n }}\n")]
G['sh_ifelse']=[(" match sharing_update{Some(val)=>{\n"," if let Some(val)=sharing_update{{\n"),("signer_seeds),val)?;\n\n }None=>{}}\n","signer_seeds),val)?;\n\n }}else{}\n")]
G['sh_isnone']=[(" match sharing_update{Some(val)=>{\n"," if sharing_update.is_none(){}else{let val=sharing_update.unwrap();{\n"),("signer_seeds),val)?;\n\n }None=>{}}\n","signer_seeds),val)?;\n\n }}\n")]
_CO='let mut target=(||->Result<Pubkey>{let st=&st;let holder_key=&holder_key;let sharing=&sk;let holder=hopt==Some(true);'
G['cf_skc']=[(_CO,_CO.replace('let sharing=&sk;','let sharing=&{sk};'))]
G['cf_hkc']=[(_CO,_CO.replace('let holder_key=&holder_key;','let holder_key=&{holder_key};'))]
G['cf_both']=[(_CO,_CO.replace('let sharing=&sk;','let sharing=&{sk};').replace('let holder_key=&holder_key;','let holder_key=&{holder_key};'))]
G['cf_order']=[(_CO,'let mut target=(||->Result<Pubkey>{let holder_key=&holder_key;let sharing=&sk;let st=&st;let holder=hopt==Some(true);')]
G['cf_skfirst']=[(_CO,'let mut target=(||->Result<Pubkey>{let sharing=&sk;let st=&st;let holder_key=&holder_key;let holder=hopt==Some(true);')]
G['cf_hopt']=[(_CO,_CO.replace('let holder=hopt==Some(true);','let hopt=hopt;let holder=hopt==Some(true);'))]
G['cf_fee']=[(_CO,_CO.replace('let holder=hopt==Some(true);','let fee=fee;let holder=hopt==Some(true);'))]
G['cf_stc']=[(_CO,_CO.replace('let st=&st;','let st=&&st;'))]
# w14a58 tafterlevy: w14a38 splicemap genes (su_tafter, s_amm_present, f6 target from curve)
G['tafter']=[('else{target=st.creator;(false,Some(args.0),true)}','else{let r=(false,Some(args.0),true);target=st.creator;r}')]
G['tafter6']=[('else{target=st.creator;(false,Some(args.0),true)}','else{let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r}')]
G['ammp']=[('let amm_frozen=!a.coin_creator_vault_ata.data_is_empty()&&token_frozen(a.coin_creator_vault_ata.as_ref())?;','let amm_present=!a.coin_creator_vault_ata.data_is_empty();let amm_frozen=amm_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?;')]
# w14a58 merges: the sharing tuple tree moved inside the validate closure (needs v7c first)
_TREE_O='if shared{if holder{(false,Some(None),false)}else{target=st.creator;(false,Some(args.0),true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)}'
_TREE_T='if shared{if holder{(false,Some(None),false)}else{let r=(false,Some(args.0),true);target=st.creator;r}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)}'
_TREE_6='if shared{if holder{(false,Some(None),false)}else{let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)}'
_OPEN='let mut target=(||->Result<Pubkey>{let st=&st;'
_OPEN2='let (target,collect_old,sharing_update,skip)=(||->Result<(Pubkey,bool,Option<Option<Pubkey>>,bool)>{let st=&st;'
def _in(tree_old,tree_new,ny=''):
    return [(_OPEN,_OPEN2),(' Ok(target)})()?;let (collect_old,sharing_update,skip)='+tree_old+';(holder,',' let mut target=target;let (collect_old,sharing_update,skip)='+tree_new+';Ok((target,collect_old,sharing_update,skip))})()?;(holder,')]
G['in_o']=_in(_TREE_O,_TREE_O)
G['in_t']=_in(_TREE_O,_TREE_T)
G['in_6']=_in(_TREE_O,_TREE_6)
# tree inside, non-holder sharing arm uses a fresh copy of new (let new=new before / after the tafter tuple)
G['in_tn1']=_in(_TREE_O,_TREE_T.replace('else{let r=(false,Some(args.0),true);','else{let new=new;let r=(false,Some(new),true);'))
G['in_tn2']=_in(_TREE_O,_TREE_T.replace('target=st.creator;r}','target=st.creator;let new=new;let _=new;r}'))
G['cuunw']=[('if let Some(f)=fee{curve.creator_fee_bps=f;}','curve.creator_fee_bps=fee.unwrap_or(curve.creator_fee_bps);')]
G['wlnot']=[('a.current_creator.is_writable==false','!a.current_creator.is_writable')]
# w14a58 validate-region micro genes (validate/entry +8 is jump-neutral on h0_cu per shift oracle)
_E_IC='return Err(error!(PumpError::InvalidCreator));'
G['v_icsplit']=[('if t==*sharing||t==*holder_key{'+_E_IC+'}','if t==*sharing{'+_E_IC+'}if t==*holder_key{'+_E_IC+'}')]
G['v_icrev']=[('if t==*sharing||t==*holder_key{','if t==*holder_key||t==*sharing{')]
G['v_icref']=[('if t==*sharing||t==*holder_key{','if &t==sharing||&t==holder_key{')]
G['v_hrnot']=[('if st.holder_reward&&!(hopt==Some(true)){','if st.holder_reward&&!holder{')]
G['v_hrne']=[('if st.holder_reward&&!(hopt==Some(true)){','if st.holder_reward&&hopt!=Some(true){')]
G['v_hdis']=[('if holder&&!st.holder_reward&&!st.holder_enabled{','if holder&&!(st.holder_reward||st.holder_enabled){')]
G['v_newsome']=[('if holder{if new.is_some(){','if holder{if let Some(_)=new{')]
G['v_newne']=[('if holder{if new.is_some(){','if holder{if new!=None{')]
G['v_hkclone']=[('*holder_key}else{','holder_key.clone()}else{')]
G['v_zero']=[('if t==Pubkey::default(){','if t==Pubkey::new_from_array([0u8;32]){')]
G['v_zeroeq']=[('if t==Pubkey::default(){','if t.eq(&Pubkey::default()){')]
G['v_cbnot']=[('let cashback=if holder{false}else{st.cashback};','let cashback=!holder&&st.cashback;')]
G['v_feeiflet']=[(' match fee{Some(f)=>{if st.quote_locked{',' if let Some(f)=fee{{if st.quote_locked{'),('CreatorFeeBpsOutOfRange));}}None=>{}}','CreatorFeeBpsOutOfRange));}}}')]
G['v_fsplit']=[('if f==0||f>st.max_fee{','if !(1..=st.max_fee).contains(&f){')]
G['v_frev']=[('if f==0||f>st.max_fee{','if f>st.max_fee||f==0{')]
G['v_hsplit']=[('if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{','if holder&&new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}else if holder{*holder_key}else{')]
G['v_tmatch']=[('  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};','  let t=match new{Some(t)=>t,None=>return Err(error!(PumpError::CtoNewCreatorRequired))};')]
# w14a58 entry / tree re-read micro genes
G['en_hk1']=[('let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;','let holder_key=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID).0;')]
G['en_hk2']=[('let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;','let (holder_key,_)=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);')]
G['en_qany']=[('a.global.whitelisted_quote_mints.contains(&q)','a.global.whitelisted_quote_mints.iter().any(|m|*m==q)')]
G['en_qnat']=[('q==Pubkey::default()||q==anchor_spl::token::spl_token::native_mint::ID||','q==anchor_spl::token::spl_token::native_mint::ID||q==Pubkey::default()||')]
G['en_qref']=[('let q=a.bonding_curve.quote_mint;','let q=&a.bonding_curve.quote_mint;'),('q==Pubkey::default()||q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(&q)','*q==Pubkey::default()||*q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(q)')]
G['en_own']=[('a.sharing_config.owner==&FEES','*a.sharing_config.owner==FEES')]
G['en_mintref']=[('let mint=a.mint.key();','let mint=*a.mint.to_account_info().key;')]
G['tr_hr']=[('(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)','(!a.bonding_curve.is_holder_reward&&st.creator!=Pubkey::default(),None,true)')]
G['tr_cb']=[('let cashback=!holder&&st.cashback;','let cashback=!holder&&a.bonding_curve.is_cashback_coin;')]
G['tr_sk']=[('let sk=a.sharing_config.key();','let sk=*a.sharing_config.key;')]
G['tr_okq']=[('let (target,sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback))?;','let (target,sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback)).map_err(|e|e)?;')]
G['tst']=[('else{let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r}','else{let r=(false,Some(args.0),true);target=st.creator;r}')]
G['noammp']=[('let amm_present=!a.coin_creator_vault_ata.data_is_empty();let amm_frozen=amm_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?;','let amm_frozen=!a.coin_creator_vault_ata.data_is_empty()&&token_frozen(a.coin_creator_vault_ata.as_ref())?;')]
