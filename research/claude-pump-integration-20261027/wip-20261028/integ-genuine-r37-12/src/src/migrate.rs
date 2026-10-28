use crate::*;
use anchor_lang::Event;
use anchor_spl::{token::Token,token_interface::{Mint,TokenAccount},token_2022::Token2022,associated_token::AssociatedToken};
use anchor_lang::solana_program::{instruction::{Instruction,AccountMeta},program::invoke_signed,program_error::ProgramError};
#[derive(Accounts)]
pub struct Migrate<'info>{
 #[account(seeds=[b"global"],bump,has_one=withdraw_authority @ PumpError::NotAuthorized)]pub global:Box<Account<'info,Global>>,
 /// CHECK: global relation.
 #[account(mut)]pub withdraw_authority:UncheckedAccount<'info>,
 pub mint:Box<InterfaceAccount<'info,Mint>>,
 #[account(mut,seeds=[b"bonding-curve",mint.key().as_ref()],bump,constraint=bonding_curve.quote_mint==Pubkey::default() @ PumpError::UnsupportedQuoteMint)]pub bonding_curve:Box<Account<'info,crate::trade_types::BondingCurve>>,
 #[account(mut,associated_token::mint=mint,associated_token::authority=bonding_curve,associated_token::token_program=mint.to_account_info().owner)]pub associated_bonding_curve:Box<InterfaceAccount<'info,TokenAccount>>,
 #[account(mut)]pub user:Signer<'info>,
 pub system_program:Program<'info,System>,pub token_program:Program<'info,Token>,pub pump_amm:Program<'info,admin_cto::Amm>,
 /// CHECK: canonical PDA.
 #[account(mut,seeds=[b"pool",&0u16.to_le_bytes(),pool_authority.key().as_ref(),mint.key().as_ref(),wsol_mint.key().as_ref()],bump,seeds::program=pump_amm.key())]pub pool:UncheckedAccount<'info>,
 /// CHECK: canonical PDA.
 #[account(mut,seeds=[b"pool-authority",mint.key().as_ref()],bump)]pub pool_authority:UncheckedAccount<'info>,
 /// CHECK: canonical ATA.
 #[account(mut,seeds=[pool_authority.key().as_ref(),mint.to_account_info().owner.as_ref(),mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]pub pool_authority_mint_account:UncheckedAccount<'info>,
 /// CHECK: canonical ATA.
 #[account(mut,seeds=[pool_authority.key().as_ref(),token_program.key().as_ref(),wsol_mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]pub pool_authority_wsol_account:UncheckedAccount<'info>,
 /// CHECK: canonical AMM config.
 #[account(seeds=[b"global_config"],bump,seeds::program=pump_amm.key())]pub amm_global_config:UncheckedAccount<'info>,
 #[account(address=anchor_spl::token::spl_token::native_mint::ID)]pub wsol_mint:Box<InterfaceAccount<'info,Mint>>,
 /// CHECK: canonical LP mint.
 #[account(mut,seeds=[b"pool_lp_mint",pool.key().as_ref()],bump,seeds::program=pump_amm.key())]pub lp_mint:AccountInfo<'info>,
 /// CHECK: canonical ATA.
 #[account(mut,seeds=[pool_authority.key().as_ref(),token_2022_program.key().as_ref(),lp_mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]pub user_pool_token_account:AccountInfo<'info>,
 /// CHECK: canonical ATA.
 #[account(mut,seeds=[pool.key().as_ref(),mint.to_account_info().owner.as_ref(),mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]pub pool_base_token_account:AccountInfo<'info>,
 /// CHECK: canonical ATA.
 #[account(mut,seeds=[pool.key().as_ref(),token_program.key().as_ref(),wsol_mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]pub pool_quote_token_account:AccountInfo<'info>,
 pub token_2022_program:Program<'info,Token2022>,pub associated_token_program:Program<'info,AssociatedToken>,
 /// CHECK: canonical AMM event PDA.
 #[account(seeds=[b"__event_authority"],bump,seeds::program=pump_amm.key())]pub pump_amm_event_authority:AccountInfo<'info>,
 /// CHECK: canonical event PDA.
 #[account(seeds=[b"__event_authority"],bump)]pub event_authority:UncheckedAccount<'info>,
 pub program:Program<'info,crate::program::PumpRecovered>,
 /// CHECK: constrained sysvar address.
 #[account(address=anchor_lang::solana_program::sysvar::rent::ID)]pub rent:UncheckedAccount<'info>,
}
fn call<'a>(program:&AccountInfo<'a>,accounts:&[(&AccountInfo<'a>,bool,bool)],data:Vec<u8>,seeds:&[&[&[u8]]])->Result<()>{let ix=Instruction{program_id:*program.key,accounts:accounts.iter().map(|(a,s,w)|if *w{AccountMeta::new(*a.key,*s)}else{AccountMeta::new_readonly(*a.key,*s)}).collect(),data};let mut infos:Vec<AccountInfo>=accounts.iter().map(|(a,_,_)|(*a).clone()).collect();infos.push(program.clone());invoke_signed(&ix,&infos,seeds)?;Ok(())}
fn move_lamports(from:&AccountInfo,to:&AccountInfo,n:u64)->Result<()>{let l=from.lamports().checked_sub(n).ok_or(ProgramError::ArithmeticOverflow)?;let r=to.lamports().checked_add(n).ok_or(ProgramError::ArithmeticOverflow)?;**from.try_borrow_mut_lamports()?=l;**to.try_borrow_mut_lamports()?=r;Ok(())}
fn amount(a:&AccountInfo)->Result<u64>{Ok(u64::from_le_bytes(a.try_borrow_data()?[64..72].try_into().unwrap()))}
pub fn execute<'info>(ctx:Context<'_, '_, '_, 'info,Migrate<'info>>)->Result<()>{
 let a=&ctx.accounts;crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.user)?;let curve=a.bonding_curve.to_account_info();require!(a.bonding_curve.complete,PumpError::BondingCurveNotComplete);if a.bonding_curve.virtual_token_reserves==0&&a.bonding_curve.virtual_quote_reserves==0&&a.bonding_curve.real_token_reserves==0&&a.bonding_curve.real_quote_reserves==0{msg!("Bonding curve already migrated");return Ok(());}
 let real_quote=a.bonding_curve.real_quote_reserves;let fee=a.global.pool_migration_fee;let base=a.associated_bonding_curve.amount;let mayhem=a.bonding_curve.is_mayhem_mode;
 let pa=a.pool_authority.to_account_info();let user=a.user.to_account_info();let mint=a.mint.to_account_info();let sys=a.system_program.to_account_info();let tok=a.token_program.to_account_info();let ata=a.associated_token_program.to_account_info();let am=a.pump_amm.to_account_info();let pool=a.pool.to_account_info();let pb=a.pool_base_token_account.to_account_info();let pq=a.pool_quote_token_account.to_account_info();let tmpb=a.pool_authority_mint_account.to_account_info();let tmpq=a.pool_authority_wsol_account.to_account_info();let wsol=a.wsol_mint.to_account_info();let lp=a.lp_mint.to_account_info();let ulp=a.user_pool_token_account.to_account_info();let t22=a.token_2022_program.to_account_info();let cfg=a.amm_global_config.to_account_info();let ev=a.pump_amm_event_authority.to_account_info();let wa=a.withdraw_authority.to_account_info();let cb=a.associated_bonding_curve.to_account_info();let rent=Rent::get()?;let base_tok=if mint.owner==tok.key{tok.clone()}else{t22.clone()};
 let mintkey=a.mint.key();let pab=[ctx.bumps.pool_authority];let pas:&[&[u8]]=&[b"pool-authority",mintkey.as_ref(),&pab];let curveb=[ctx.bumps.bonding_curve];let cs:&[&[u8]]=&[b"bonding-curve",mintkey.as_ref(),&curveb];
 // Original transfers migration liquidity to its signer PDA before paying CPI rents.
 move_lamports(&curve,&pa,fee)?;
 for (dest,wallet,m,token) in [(&pb,&pool,&mint,&base_tok),(&pq,&pool,&wsol,&tok),(&tmpb,&pa,&mint,&base_tok),(&tmpq,&pa,&wsol,&tok)]{call(&ata,&[(&pa,true,true),(dest,false,true),(wallet,false,false),(m,false,false),(&sys,false,false),(token,false,false),(&curve,false,false)],vec![1],&[pas])?;}
 if base>0{let mut transfer=vec![12];transfer.extend_from_slice(&base.to_le_bytes());transfer.push(a.mint.decimals);call(&base_tok,&[(&cb,false,true),(&mint,false,false),(&tmpb,false,true),(&curve,true,false)],transfer,&[cs])?;}let base=pool_authority_mint_token_account(a)?.amount;
 let quote=real_quote.checked_add(a.bonding_curve.post_complete_quote_in)
  .ok_or_else(||error!(PumpError::Overflow))?
  .checked_sub(fee)
  .ok_or_else(||error!(PumpError::Overflow))?;
 // Allocate quote funding from signer PDA into native token account.
 move_lamports(&curve,&tmpq,quote)?;
 call(&tok,&[(&tmpq,false,true),(&a.rent.to_account_info(),false,false),(&curve,false,false)],vec![17],&[])?;
 let creator=a.bonding_curve.creator;let cpi_accounts=pump_amm::cpi::accounts::CreatePool{pool:pool.clone(),global_config:cfg.clone(),creator:pa.clone(),base_mint:mint.clone(),quote_mint:wsol.clone(),lp_mint:lp.clone(),user_base_token_account:tmpb.clone(),user_quote_token_account:tmpq.clone(),user_pool_token_account:ulp.clone(),pool_base_token_account:pb.clone(),pool_quote_token_account:pq.clone(),system_program:sys.clone(),token_2022_program:t22.clone(),base_token_program:base_tok.clone(),quote_token_program:tok.clone(),associated_token_program:ata.clone(),event_authority:ev.clone(),program:am.clone()};
 pump_amm::cpi::create_pool(CpiContext::new_with_signer(am.clone(),cpi_accounts,&[pas]),0,base,quote,creator,mayhem,pump_amm::types::OptionBool(a.bonding_curve.is_cashback_coin),pump_amm::types::OptionU64(a.bonding_curve.creator_fee_bps),pump_amm::types::OptionBool(a.bonding_curve.can_edit_creator_fee),pump_amm::types::OptionBool(a.bonding_curve.is_holder_reward))?;
 if !mayhem && (ctx.remaining_accounts.len()==2 || native_payments::boost_enabled(&cfg)) {
  require!(ctx.remaining_accounts.len()==2,PumpError::NotEnoughRemainingAccounts);
  let boost=&ctx.remaining_accounts[0];let vault=&ctx.remaining_accounts[1];
  let funding=Rent::get()?.minimum_balance(165);
  native_payments::transfer_native(a.system_program.as_ref(),&a.user,&a.pool_authority,funding)?;
  pump_amm::cpi::init_boost(CpiContext::new_with_signer(am.clone(),pump_amm::cpi::accounts::InitBoost{pool:pool.clone(),global_config:cfg.clone(),creator:pa.clone(),base_mint:mint.clone(),quote_mint:wsol.clone(),pool_base_token_account:pb.clone(),pool_quote_token_account:pq.clone(),boost_vault_authority:boost.clone(),boost_vault:vault.clone(),quote_token_program:tok.clone(),system_program:sys.clone(),associated_token_program:ata.clone(),event_authority:ev.clone(),program:am.clone()},&[pas]))?;
 }
 for (temp,token) in [(&tmpb,&base_tok),(&tmpq,&tok)]{call(token,&[(temp,false,true),(&wa,false,true),(&pa,true,false)],vec![9],&[pas])?;}
 let burn_amount=amount(&ulp)?;anchor_spl::token_2022::burn(CpiContext::new_with_signer(t22.clone(),anchor_spl::token_2022::Burn{mint:lp.clone(),from:ulp.clone(),authority:pa.clone()},&[pas]),burn_amount)?;close_pool_authority_account(a,ctx.bumps.pool_authority,&a.user_pool_token_account)?;
 refund_pool_authority(a,ctx.bumps.pool_authority,&wa,pa.lamports())?;

 {let c=&mut ctx.accounts.bonding_curve;c.real_quote_reserves=0;c.real_token_reserves=0;c.virtual_quote_reserves=0;c.virtual_token_reserves=0;}
 let a=&ctx.accounts;
 let event=CompletePumpAmmMigrationEvent{user:a.user.key(),mint:mintkey,mint_amount:base,sol_amount:quote,pool_migration_fee:fee,bonding_curve:a.bonding_curve.key(),timestamp:Clock::get()?.unix_timestamp,pool:a.pool.key(),quote_mint:Pubkey::default()};emit!(event.clone());let mut event_data=vec![228,69,165,46,81,203,154,29];event_data.extend_from_slice(&event.data());let eb=[ctx.bumps.event_authority];call(&a.program.to_account_info(),&[(&a.event_authority.to_account_info(),true,false)],event_data,&[&[b"__event_authority",&eb]])?;Ok(())
}
#[event]#[derive(Clone)]pub struct CompletePumpAmmMigrationEvent{pub user:Pubkey,pub mint:Pubkey,pub mint_amount:u64,pub sol_amount:u64,pub pool_migration_fee:u64,pub bonding_curve:Pubkey,pub timestamp:i64,pub pool:Pubkey,pub quote_mint:Pubkey}

// The original migration skips an empty refund before constructing signer seeds.
#[inline(never)]
fn refund_pool_authority<'info>(a:&Migrate<'info>,bump:u8,destination:&AccountInfo<'info>,amount:u64)->Result<()>{
 if amount==0{return Ok(());}
 let transfer=|signer_seeds:&[&[&[u8]];1]|crate::migrate::transfer_native(a.system_program.as_ref(),&a.pool_authority,destination,amount,signer_seeds);
 transfer(&[&[b"pool-authority",a.mint.key().as_ref(),&[bump]]])
}

#[inline(never)]
pub fn transfer_native<'info>(system_program:&AccountInfo<'info>,source:&UncheckedAccount<'info>,destination:&AccountInfo<'info>,amount:u64,signer_seeds:&[&[&[u8]];1])->Result<()>{
 if amount==0{return Ok(());}
 anchor_lang::system_program::transfer(CpiContext::new_with_signer(system_program.clone(),anchor_lang::system_program::Transfer{from:source.to_account_info(),to:destination.clone()},signer_seeds),amount)
}

#[path="migration_native_payments.rs"]
pub mod native_payments;

pub fn close_pool_authority_account<'info>(a:&Migrate<'info>,bump:u8,account:&AccountInfo<'info>)->Result<()>{
 close_token_account(a,account,&[&[b"pool-authority",a.mint.key().as_ref(),&[bump]]])
}

fn close_token_account<'info>(a:&Migrate<'info>,account:&AccountInfo<'info>,signer_seeds:&[&[&[u8]]])->Result<()>{
 anchor_spl::token_2022::close_account(CpiContext::new_with_signer(a.token_2022_program.to_account_info(),anchor_spl::token_2022::CloseAccount{account:account.clone(),destination:a.withdraw_authority.to_account_info(),authority:a.pool_authority.to_account_info()},signer_seeds))
}

#[inline(never)]
pub fn pool_authority_mint_token_account(a:&Migrate)->Result<TokenAccount>{
 let data=a.pool_authority_mint_account.try_borrow_data()?;
 TokenAccount::try_deserialize_unchecked(&mut &data[..])
}
