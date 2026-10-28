use anchor_lang::prelude::*;
use crate::{PumpError,distribution::{FEES,SharingConfig},trade_types::BondingCurve};
#[derive(Accounts)]
pub struct GetMinimumDistributableFee<'info>{
 pub mint:InterfaceAccount<'info,anchor_spl::token_interface::Mint>,
 #[account(seeds=[b"bonding-curve",mint.key().as_ref()],bump,constraint=bonding_curve.creator==sharing_config.key() @ PumpError::BondingCurveAndSharingConfigCreatorMismatch)]pub bonding_curve:Account<'info,BondingCurve>,
 #[account(seeds=[b"sharing-config",mint.key().as_ref()],bump,seeds::program=FEES,has_one=mint @ PumpError::MintDoesNotMatchBondingCurve)]pub sharing_config:Account<'info,SharingConfig>,
 /// CHECK: only seeds and available lamports are used by this readonly query.
 #[account(seeds=[b"creator-vault",bonding_curve.creator.as_ref()],bump)]pub creator_vault:AccountInfo<'info>,
}
#[event]
#[derive(Clone)]
pub struct MinimumDistributableFeeEvent{pub minimum_required:u64,pub distributable_fees:u64,pub can_distribute:bool}
pub fn execute<'info>(ctx:Context<'_, '_, '_, 'info,GetMinimumDistributableFee<'info>>)->Result<MinimumDistributableFeeEvent>{
 let a=ctx.accounts;
 let rent=Rent::get()?;
 let (_,minimum_distributable,minimum_required,distributable_fees)=crate::distribution::get_distribution_amounts(&rent,&a.sharing_config.shareholders,ctx.remaining_accounts,&a.creator_vault)?;
 let event=MinimumDistributableFeeEvent{minimum_required,distributable_fees,can_distribute:distributable_fees>=minimum_distributable};emit!(event.clone());Ok(event)
}
