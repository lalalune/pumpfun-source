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
