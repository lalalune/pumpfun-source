use anchor_lang::prelude::*;
use crate::{PumpError,trade_types::BondingCurve,distribution::{SharingConfig,FEES}};
#[derive(Accounts)]
pub struct MigrateBondingCurveCreator<'info>{
 pub mint:InterfaceAccount<'info,anchor_spl::token_interface::Mint>,
 #[account(mut,seeds=[b"bonding-curve",mint.key().as_ref()],bump)]pub bonding_curve:Account<'info,BondingCurve>,
 #[account(seeds=[b"sharing-config",mint.key().as_ref()],bump,seeds::program=FEES,has_one=mint @ PumpError::MintDoesNotMatchBondingCurve,constraint=sharing_config.admin==bonding_curve.creator @ PumpError::BondingCurveAndSharingConfigCreatorMismatch)]pub sharing_config:Account<'info,SharingConfig>,
 /// CHECK: canonical event authority.
 #[account(seeds=[b"__event_authority"],bump)]pub event_authority:AccountInfo<'info>,
 /// CHECK: original validates this only through event CPI invocation.
 pub program:AccountInfo<'info>,
}
#[event]
#[derive(Clone)]pub struct MigrateBondingCurveCreatorEvent{pub timestamp:i64,pub mint:Pubkey,pub bonding_curve:Pubkey,pub sharing_config:Pubkey,pub old_creator:Pubkey,pub new_creator:Pubkey}
pub fn execute(mut ctx:Context<MigrateBondingCurveCreator>)->Result<()>{
 let a=&mut ctx.accounts;require!(!a.bonding_curve.is_holder_reward,PumpError::HolderRewardCreatorImmutable);require!(a.bonding_curve.creator_fee==0,PumpError::CreatorFeesNotSwept);
 let old_creator=a.bonding_curve.creator;let new_creator=a.sharing_config.key();a.bonding_curve.creator=new_creator;
 let event=MigrateBondingCurveCreatorEvent{timestamp:Clock::get()?.unix_timestamp,mint:a.mint.key(),bonding_curve:a.bonding_curve.key(),sharing_config:a.sharing_config.key(),old_creator,new_creator};emit!(event);emit_cpi!(event);Ok(())
}
