use anchor_lang::prelude::*;
use crate::{Global,PumpError};
#[event_cpi]
#[derive(Accounts)]
pub struct SetParams<'info>{
 #[account(mut,seeds=[b"global"],bump,has_one=authority @ PumpError::NotAuthorized)]pub global:Account<'info,Global>,
 #[account(mut)]pub authority:Signer<'info>,
}
#[event]
#[derive(Clone)]
pub struct SetParamsEvent{pub initial_virtual_token_reserves:u64,pub initial_virtual_sol_reserves:u64,pub initial_real_token_reserves:u64,pub final_real_sol_reserves:u64,pub token_total_supply:u64,pub fee_basis_points:u64,pub withdraw_authority:Pubkey,pub enable_migrate:bool,pub pool_migration_fee:u64,pub creator_fee_basis_points:u64,pub fee_recipients:[Pubkey;8],pub timestamp:i64,pub set_creator_authority:Pubkey,pub admin_set_creator_authority:Pubkey}
pub fn execute(ctx:Context<SetParams>,initial_virtual_token_reserves:u64,initial_virtual_sol_reserves:u64,initial_real_token_reserves:u64,token_total_supply:u64,fee_basis_points:u64,withdraw_authority:Pubkey,enable_migrate:bool,pool_migration_fee:u64,creator_fee_basis_points:u64,set_creator_authority:Pubkey,admin_set_creator_authority:Pubkey)->Result<()>{
 require_gte!(ctx.remaining_accounts.len(),8,PumpError::NotEnoughRemainingAccounts);
 let rent=Rent::get()?;let mut recipients=[Pubkey::default();8];
 for (i,a) in ctx.remaining_accounts[..8].iter().enumerate(){require!(a.key()!=Pubkey::default(),PumpError::AllFeeRecipientsShouldBeNonZero);if !rent.is_exempt(a.lamports(),a.data_len()){return Err(error!(anchor_lang::error::ErrorCode::ConstraintRentExempt).with_account_name(format!("fee_recipients[{}]",i)));}recipients[i]=a.key();}
 require!(recipients.windows(2).all(|w|w[0]<w[1]),PumpError::UnsortedNotUniqueFeeRecipients);
 require_gt!(token_total_supply,initial_real_token_reserves,PumpError::InitialRealTokenReservesShouldBeLessThanTokenTotalSupply);
 require_gt!(initial_virtual_token_reserves,initial_real_token_reserves,PumpError::InitialVirtualTokenReservesShouldBeGreaterThanInitialRealTokenReserves);
 require_gte!(1000,fee_basis_points,PumpError::FeeBasisPointsGreaterThanMaximum);
 require_keys_neq!(withdraw_authority,Pubkey::default(),PumpError::AllZerosWithdrawAuthority);
 let final_value=(initial_virtual_token_reserves as u128)*(initial_virtual_sol_reserves as u128)/(initial_virtual_token_reserves-initial_real_token_reserves) as u128-(initial_virtual_sol_reserves as u128);
 let final_real_sol_reserves=u64::try_from(final_value).map_err(|_|error!(PumpError::Truncation))?;
 require_gt!(final_real_sol_reserves,pool_migration_fee,PumpError::PoolMigrationFeeShouldBeLessThanFinalRealSolReserves);
 require_gte!(1000,creator_fee_basis_points,PumpError::FeeBasisPointsGreaterThanMaximum);
 let g=&mut ctx.accounts.global;
 g.initial_virtual_token_reserves=initial_virtual_token_reserves;
 g.initial_virtual_sol_reserves=initial_virtual_sol_reserves;
 g.initial_real_token_reserves=initial_real_token_reserves;
 g.token_total_supply=token_total_supply;
 g.fee_basis_points=fee_basis_points;
 g.withdraw_authority=withdraw_authority;
 g.enable_migrate=enable_migrate;
 g.pool_migration_fee=pool_migration_fee;
 g.creator_fee_basis_points=creator_fee_basis_points;
 g.set_creator_authority=set_creator_authority;
 g.admin_set_creator_authority=admin_set_creator_authority;
 g.fee_recipient=recipients[0];g.fee_recipients.copy_from_slice(&recipients[1..]);
 let event=SetParamsEvent{initial_virtual_token_reserves,initial_virtual_sol_reserves,initial_real_token_reserves,token_total_supply,fee_basis_points,withdraw_authority,enable_migrate,pool_migration_fee,creator_fee_basis_points,set_creator_authority,admin_set_creator_authority,final_real_sol_reserves,fee_recipients:recipients,timestamp:Clock::get()?.unix_timestamp};emit!(event.clone());emit_cpi!(event);Ok(())
}
