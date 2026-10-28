use crate::*;
use anchor_spl::{token::{self,Mint,Token,TokenAccount},associated_token::AssociatedToken};
use anchor_lang::solana_program::{instruction::{Instruction,AccountMeta},program::invoke_signed};
pub use anchor_spl::metadata::Metadata as MetadataProgram;
#[event_cpi]
#[derive(Accounts)]
pub struct Create<'info>{
 #[account(init,payer=user,mint::decimals=6,mint::authority=mint_authority)]
 pub mint:Box<Account<'info,Mint>>,
 /// CHECK: canonical program mint authority.
 #[account(seeds=[b"mint-authority"],bump)]
 pub mint_authority:UncheckedAccount<'info>,
 #[account(init,payer=user,space=166,seeds=[b"bonding-curve",mint.key().as_ref()],bump)]
 pub bonding_curve:Box<Account<'info,trade_types::BondingCurve>>,
 #[account(init,payer=user,associated_token::mint=mint,associated_token::authority=bonding_curve)]
 pub associated_bonding_curve:Box<Account<'info,TokenAccount>>,
 #[account(seeds=[b"global"],bump)]
 pub global:Account<'info,Global>,
 pub mpl_token_metadata:Program<'info,MetadataProgram>,
 /// CHECK: canonical metadata account, allocated by the metadata program.
 #[account(mut,seeds=[b"metadata",anchor_spl::metadata::ID.as_ref(),mint.key().as_ref()],bump,seeds::program=mpl_token_metadata.key())]
 pub metadata:UncheckedAccount<'info>,
 #[account(mut)]pub user:Signer<'info>,
 pub system_program:Program<'info,System>,
 pub token_program:Program<'info,Token>,
 pub associated_token_program:Program<'info,AssociatedToken>,
 pub rent:Sysvar<'info,Rent>,
}
pub fn execute(ctx:Context<Create>,name:String,symbol:String,uri:String,creator:Pubkey)->Result<()>{
 require_keys_neq!(creator,Pubkey::default(),PumpError::CreatorShouldNotBeZero);
 let a=&ctx.accounts;let bump=[ctx.bumps.mint_authority];let seeds:&[&[u8]]=&[b"mint-authority",&bump];
 let metadata_data=anchor_spl::metadata::mpl_token_metadata::types::DataV2{name:name.clone(),symbol:symbol.clone(),uri:uri.clone(),seller_fee_basis_points:0,creators:Some(vec![anchor_spl::metadata::mpl_token_metadata::types::Creator{address:creator,verified:false,share:100}]),collection:None,uses:None};
 anchor_spl::metadata::create_metadata_accounts_v3(
  CpiContext::new_with_signer(a.mpl_token_metadata.to_account_info(),anchor_spl::metadata::CreateMetadataAccountsV3{
   metadata:a.metadata.to_account_info(),mint:a.mint.to_account_info(),mint_authority:a.mint_authority.to_account_info(),payer:a.user.to_account_info(),update_authority:a.mint_authority.to_account_info(),system_program:a.system_program.to_account_info(),rent:a.rent.to_account_info(),
  },&[seeds]),
  metadata_data,
  false,false,None,
 )?;
 token::mint_to(CpiContext::new_with_signer(a.token_program.to_account_info(),token::MintTo{mint:a.mint.to_account_info(),to:a.associated_bonding_curve.to_account_info(),authority:a.mint_authority.to_account_info()},&[seeds]),a.global.token_total_supply)?;
 token::set_authority(CpiContext::new_with_signer(a.token_program.to_account_info(),token::SetAuthority{current_authority:a.mint_authority.to_account_info(),account_or_mint:a.mint.to_account_info()},&[seeds]),token::spl_token::instruction::AuthorityType::MintTokens,None)?;
 let event=CreateEvent{name,symbol,uri,mint:a.mint.key(),bonding_curve:a.bonding_curve.key(),user:a.user.key(),creator,timestamp:Clock::get()?.unix_timestamp,virtual_token_reserves:a.global.initial_virtual_token_reserves,virtual_sol_reserves:a.global.initial_virtual_sol_reserves,real_token_reserves:a.global.initial_real_token_reserves,token_total_supply:a.global.token_total_supply,token_program:a.token_program.key(),is_mayhem_mode:false,is_cashback_enabled:false,quote_mint:Pubkey::default(),virtual_quote_reserves:a.global.initial_virtual_sol_reserves,creator_fee_bps:0,is_holder_reward:false,depth:0};
 let g=&ctx.accounts.global;let curve=&mut ctx.accounts.bonding_curve;curve.virtual_token_reserves=g.initial_virtual_token_reserves;curve.virtual_quote_reserves=g.initial_virtual_sol_reserves;curve.real_token_reserves=g.initial_real_token_reserves;curve.token_total_supply=g.token_total_supply;curve.creator=creator;curve.initial_virtual_quote_reserves=g.initial_virtual_sol_reserves;
 emit!(event.clone());emit_cpi!(event);Ok(())
}
pub use crate::CreateEvent;
