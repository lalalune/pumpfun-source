use anchor_lang::prelude::*;
#[event_cpi]#[derive(Accounts)]pub struct CollectCreatorFee<'info>{#[doc="CHECK: payout destination is bound to the vault PDA."]#[account(mut)]pub creator:AccountInfo<'info>,#[doc="CHECK: original defers owner/data restrictions to System transfer."]#[account(mut,seeds=[b"creator-vault",creator.key().as_ref()],bump)]pub creator_vault:AccountInfo<'info>,pub system_program:Program<'info,System>,}
#[event_cpi]
#[derive(Accounts)]
pub struct CollectCreatorFeeV2<'info>{
 /// CHECK: recipient only tied to vault/ATA seeds.
 #[account(mut)]pub creator:AccountInfo<'info>,
 /// CHECK: token program validates data only during positive token transfer.
 #[account(mut,seeds=[creator.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]pub creator_token_account:UncheckedAccount<'info>,
 /// CHECK: address constrained, native transfer defers owner/data checks.
 #[account(mut,seeds=[b"creator-vault",creator.key().as_ref()],bump)]pub creator_vault:AccountInfo<'info>,
 /// CHECK: address constrained, token program validates on transfer.
 #[account(mut,seeds=[creator_vault.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]pub creator_vault_token_account:UncheckedAccount<'info>,
 pub quote_mint:Box<InterfaceAccount<'info,anchor_spl::token_interface::Mint>>,
 pub quote_token_program:Interface<'info,anchor_spl::token_interface::TokenInterface>,
 pub associated_token_program:Program<'info,anchor_spl::associated_token::AssociatedToken>,
 pub system_program:Program<'info,System>,
}
// layout-pad(173): aligns the next Source site with the original line


















































































pub fn collect_creator_fee(ctx:Context<crate::CollectCreatorFee>)->Result<()>{
 let creator_vault=&ctx.accounts.creator_vault;match *ctx.accounts.creator.owner!=crate::distribution::FEES{false=>err!(crate::PumpError::UnableToDistributeCreatorVaultMigratedToSharingConfig),true=>{
 if ctx.accounts.creator.executable{msg!("Creator account is executable, so it cannot receive lamports");return Ok(());}
 let rent=Rent::get()?;
 let amount=creator_vault.lamports().saturating_sub(rent.minimum_balance(0));
 if amount==0{msg!("No creator fee to collect");return Ok(());}
 if ctx.accounts.creator.lamports().saturating_add(amount)<rent.minimum_balance(ctx.accounts.creator.data_len()){msg!("Creator account does not have enough rent-exemption lamports");return Ok(());}
 let creator=ctx.accounts.creator.key();
 transfer_lamports(&ctx.accounts.system_program,creator_vault,&ctx.accounts.creator,amount,&[&[b"creator-vault",creator.as_ref(),&[ctx.bumps.creator_vault]]])?;
 let event=crate::CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,creator,creator_fee:amount,quote_mint:Pubkey::default()};emit!(event);emit_cpi!(event);Ok(())
}}}
#[inline]fn transfer_lamports<'info>(system_program:&Program<'info,System>,from:impl ToAccountInfo<'info>,to:impl ToAccountInfo<'info>,amount:u64,signer_seeds:&[&[&[u8]]])->Result<()>{anchor_lang::system_program::transfer(CpiContext::new_with_signer(system_program.to_account_info(),anchor_lang::system_program::Transfer{from:from.to_account_info(),to:to.to_account_info()},signer_seeds),amount)}

pub fn execute(ctx:Context<CollectCreatorFeeV2>)->Result<()>{
 let a=&ctx.accounts;
 if let Some((amount,quote_mint))=collect(&a.creator,a.creator_token_account.as_ref(),&a.creator_vault,ctx.bumps.creator_vault,a.creator_vault_token_account.as_ref(),a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),&a.quote_token_program,a.system_program.as_ref())?{
  let event=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,creator:a.creator.key(),creator_fee:amount,quote_mint};emit!(event);emit_cpi!(event);
 }
 Ok(())
}







































































pub fn collect<'info>(
 creator:&AccountInfo<'info>,creator_token_account:&AccountInfo<'info>,creator_vault:&AccountInfo<'info>,
 creator_vault_bump:u8,creator_vault_token_account:&AccountInfo<'info>,decimals:u8,quote_mint:&AccountInfo<'info>,
 quote_token_program:&Interface<'info,anchor_spl::token_interface::TokenInterface>,system_program:&AccountInfo<'info>,
)->Result<Option<(u64,Pubkey)>>{
 require!(*creator.owner!=crate::distribution::FEES,crate::PumpError::UnableToDistributeCreatorVaultMigratedToSharingConfig);
 if creator.executable{msg!("Creator account is executable, so it cannot receive lamports");return Ok(None);}
 let creator_key=creator.key();
 if quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID{
  let rent=Rent::get()?;
  let amount=creator_vault.lamports().saturating_sub(rent.minimum_balance(0));
  if amount==0{msg!("No creator fee to collect");return Ok(None);}
  if creator.lamports().saturating_add(amount)<rent.minimum_balance(creator.data_len()){msg!("Creator account does not have enough rent-exemption lamports");return Ok(None);}
  transfer_native(system_program,creator_vault,creator,amount,&[&[b"creator-vault",creator_key.as_ref(),&[creator_vault_bump]]])?;
  return Ok(Some((amount,Pubkey::default())));
 }
 let amount={let data=creator_vault_token_account.try_borrow_data()?;anchor_spl::token_interface::TokenAccount::try_deserialize(&mut &data[..])?.amount};
 if amount==0{msg!("No creator fee to collect");return Ok(None);}
 transfer_tokens(quote_token_program,creator_vault_token_account,creator_token_account,creator_vault,decimals,quote_mint,amount,&[&[b"creator-vault",creator_key.as_ref(),&[creator_vault_bump]]])?;
 Ok(Some((amount,quote_mint.key())))
}

pub(crate) use crate::payments::collect_transfer_native as transfer_native;
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad

pub use crate::payments::collect_transfer_tokens as transfer_tokens;
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad

// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad

pub use crate::payments::collect_transfer_vault_tokens as transfer_vault_tokens;
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad

pub use crate::payments::collect_transfer_user_tokens_ref as transfer_user_tokens_ref;
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad

pub use crate::payments::collect_transfer_user_quote_tokens as transfer_user_quote_tokens;
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
#[event]
#[derive(Clone)]
pub struct CollectCreatorFeeEvent{pub timestamp:i64,pub creator:Pubkey,pub creator_fee:u64,pub quote_mint:Pubkey}
