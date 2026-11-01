//! Partial social-fee behavior integrated from the independently validated draft.
use anchor_lang::prelude::*;
use crate::FeeError;
use crate::types::FeeProgramGlobal;
 pub fn claim_v2(ctx:Context<ClaimSocialFeePdaV2>,_user_id:String,_platform:u8)->Result<Option<SocialFeePdaClaimed>> {
  if ctx.accounts.fee_program_global.disable_flags&2!=0 {msg!("ClaimSocialFeePda is currently disabled");return Err(FeeError::FeatureDeactivated.into());}
  let timestamp=Clock::get()?.unix_timestamp;let now=timestamp as u64;
  let state=&mut ctx.accounts.social_fee_pda;
  let rate_limit=ctx.accounts.fee_program_global.claim_rate_limit; let limited=rate_limit!=0 && state.last_claimed!=0 && now<state.last_claimed.saturating_add(rate_limit); if limited {msg!("Claim rate limit exceeded");return Ok(None);}
  if ctx.accounts.recipient.executable {msg!("Recipient account is executable, so it cannot receive lamports");return Ok(None);}
  let native=ctx.accounts.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;
  if native {
   let balance=state.to_account_info().lamports();
   let amount=balance.saturating_sub(Rent::get()?.minimum_balance(179));
   if amount==0 {msg!("No fees available to claim");return Ok(None);}
   if ctx.accounts.recipient.executable {msg!("Recipient account is executable, so it cannot receive lamports");return Ok(None);}
   let info=state.to_account_info();let recipient=ctx.accounts.recipient.to_account_info();let before=recipient.lamports();
   let mut from=info.try_borrow_mut_lamports()?;let mut to=recipient.try_borrow_mut_lamports()?;**from=(**from).saturating_sub(amount);**to=(**to).saturating_add(amount);
   let after=**to;state.total_claimed=state.total_claimed.saturating_add(amount);  state.last_claimed=now;   let event=SocialFeePdaClaimed{timestamp,user_id:state.user_id.clone(),platform:state.platform,social_fee_pda:state.key(),recipient:ctx.accounts.recipient.key(),social_claim_authority:ctx.accounts.social_claim_authority.key(),amount_claimed:amount,claimable_before:amount,lifetime_claimed:state.total_claimed,recipient_balance_before:before,recipient_balance_after:after,quote_mint:Pubkey::default(),lifetime_stable_claimed:state.total_stable_claimed};   emit!(event);emit_cpi!(event);return Ok(Some(event));
  }
  {
   crate::instructions::fee_sharing::admit_associated_token_account(
    &ctx.accounts.associated_social_fee_pda,&state.to_account_info(),ctx.accounts.quote_mint.key(),
    ctx.accounts.quote_token_program.key(),&ctx.accounts.quote_mint.to_account_info(),&ctx.accounts.quote_token_program,
    false,&ctx.accounts.social_claim_authority,&ctx.accounts.system_program)?;
   crate::instructions::fee_sharing::admit_associated_token_account(
    &ctx.accounts.associated_recipient,&ctx.accounts.recipient.to_account_info(),ctx.accounts.quote_mint.key(),
    ctx.accounts.quote_token_program.key(),&ctx.accounts.quote_mint.to_account_info(),&ctx.accounts.quote_token_program,
    true,&ctx.accounts.social_claim_authority,&ctx.accounts.system_program)?;
   let amount={
    let data=ctx.accounts.associated_social_fee_pda.try_borrow_data()?;
    anchor_spl::token_interface::TokenAccount::try_deserialize(&mut &data[..])?.amount
   };
   if amount==0 {msg!("No fees available to claim");return Ok(None);}
   let before={
    let data=ctx.accounts.associated_recipient.try_borrow_data()?;
    anchor_spl::token_interface::TokenAccount::try_deserialize(&mut &data[..]).map(|account|account.amount).unwrap_or_default()
   };
   let bump=state.bump;let user_id=state.user_id.as_bytes().to_vec();let platform=state.platform;let signer_seeds:&[&[&[u8]]]=&[&[b"social-fee-pda",user_id.as_slice(),&[platform],&[bump]]];
   anchor_spl::token_interface::transfer_checked(CpiContext::new_with_signer(ctx.accounts.quote_token_program.to_account_info(),anchor_spl::token_interface::TransferChecked{from:ctx.accounts.associated_social_fee_pda.to_account_info(),mint:ctx.accounts.quote_mint.to_account_info(),to:ctx.accounts.associated_recipient.to_account_info(),authority:state.to_account_info()},signer_seeds),amount,ctx.accounts.quote_mint.decimals)?;
   let after=before.saturating_add(amount);
   state.total_stable_claimed=state.total_stable_claimed.saturating_add(amount);  state.last_claimed=now;   let event=SocialFeePdaClaimed{timestamp,user_id:state.user_id.clone(),platform:state.platform,social_fee_pda:state.key(),recipient:ctx.accounts.recipient.key(),social_claim_authority:ctx.accounts.social_claim_authority.key(),amount_claimed:amount,claimable_before:amount,lifetime_claimed:state.total_claimed,recipient_balance_before:before,recipient_balance_after:after,quote_mint:ctx.accounts.quote_mint.key(),lifetime_stable_claimed:state.total_stable_claimed};   emit!(event);emit_cpi!(event);return Ok(Some(event));
  }



 }










 pub fn claim(ctx:Context<ClaimSocialFeePda>,user_id:String,platform:u8)->Result<Option<SocialFeePdaClaimed>> {
  if ctx.accounts.fee_program_global.disable_flags&2!=0 {
   msg!("ClaimSocialFeePda is currently disabled");
   return Err(FeeError::FeatureDeactivated.into());
  }
  let state=&mut ctx.accounts.social_fee_pda;
  let timestamp=Clock::get()?.unix_timestamp;let now=timestamp as u64;
  let rate_limit=ctx.accounts.fee_program_global.claim_rate_limit;
  let limited=rate_limit!=0 && state.last_claimed!=0 && now<state.last_claimed.saturating_add(rate_limit); if limited {
   msg!("Claim rate limit exceeded");return Ok(None);
  }
  let balance=state.to_account_info().lamports();
  let amount=balance.saturating_sub(Rent::get()?.minimum_balance(179));
  if amount==0 {msg!("No fees available to claim");return Ok(None);}
  if ctx.accounts.recipient.executable {msg!("Recipient account is executable, so it cannot receive lamports");return Ok(None);}
  let from_info=state.to_account_info();
  let to_info=ctx.accounts.recipient.to_account_info();
  let before=to_info.lamports();
  let mut from=from_info.try_borrow_mut_lamports()?;
  let mut to=to_info.try_borrow_mut_lamports()?;
  **from=(**from).saturating_sub(amount);
  **to=(**to).saturating_add(amount);
  let after=**to; state.total_claimed=state.total_claimed.saturating_add(amount);state.last_claimed=now;
  let event=SocialFeePdaClaimed {timestamp,user_id:state.user_id.clone(),platform:state.platform,social_fee_pda:state.key(),recipient:ctx.accounts.recipient.key(),social_claim_authority:ctx.accounts.social_claim_authority.key(),amount_claimed:amount,claimable_before:amount,lifetime_claimed:state.total_claimed,recipient_balance_before:before,recipient_balance_after:after,quote_mint:Pubkey::default(),lifetime_stable_claimed:state.total_stable_claimed};
  emit!(event);emit_cpi!(event);Ok(Some(event))
 }
pub use crate::instructions::fee_sharing::create_social_fee_pda::*;











pub use crate::state::SocialFeePda;
pub use crate::instructions::fee_sharing::create_social_fee_pda::SocialFeePdaCreated;


#[derive(Accounts)]
#[instruction(user_id:String,platform:u8)]
pub struct ClaimSocialFeePda<'info>{
 /// CHECK: arbitrary recipient validated in handler.
 #[account(mut)]pub recipient:UncheckedAccount<'info>,
 #[account(mut,seeds=[b"social-fee-pda",user_id.as_bytes(),&[platform]],bump=social_fee_pda.bump)]pub social_fee_pda:Account<'info,SocialFeePda>,
 #[account(seeds=[b"fee-program-global"],bump=fee_program_global.bump,has_one=social_claim_authority @ FeeError::NotAuthorized)]pub fee_program_global:Account<'info,FeeProgramGlobal>,
 pub social_claim_authority:Signer<'info>,
 /// CHECK: event PDA.
 #[account(seeds=[b"__event_authority"],bump)]pub event_authority:AccountInfo<'info>,
 /// CHECK: event CPI target.
 pub program:AccountInfo<'info>,
}
pub use crate::instructions::fee_sharing::claim_social_fee_pda::SocialFeePdaClaimed;



#[derive(Accounts)]
#[instruction(user_id:String,platform:u8)]
pub struct ClaimSocialFeePdaV2<'info>{
 /// CHECK: recipient.
 #[account(mut)]pub recipient:UncheckedAccount<'info>,
 #[account(mut,seeds=[b"social-fee-pda",user_id.as_bytes(),&[platform]],bump=social_fee_pda.bump)]pub social_fee_pda:Account<'info,SocialFeePda>,
 #[account(mut)]pub quote_mint:Box<InterfaceAccount<'info,anchor_spl::token_interface::Mint>>,
 /// CHECK: canonical ATA; data validated on token branch.
 #[account(mut,seeds=[social_fee_pda.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]pub associated_social_fee_pda:UncheckedAccount<'info>,
 /// CHECK: canonical ATA; data validated on token branch.
 #[account(mut,seeds=[recipient.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]pub associated_recipient:UncheckedAccount<'info>,
 pub quote_token_program:Interface<'info,anchor_spl::token_interface::TokenInterface>,
 pub associated_token_program:Program<'info,anchor_spl::associated_token::AssociatedToken>,
 #[account(seeds=[b"fee-program-global"],bump=fee_program_global.bump,has_one=social_claim_authority @ FeeError::NotAuthorized)]pub fee_program_global:Account<'info,FeeProgramGlobal>,
 pub social_claim_authority:Signer<'info>,
 pub system_program:Program<'info,System>,
 /// CHECK: event PDA.
 #[account(seeds=[b"__event_authority"],bump)]pub event_authority:AccountInfo<'info>,
 /// CHECK: event CPI target.
 pub program:AccountInfo<'info>,
}
