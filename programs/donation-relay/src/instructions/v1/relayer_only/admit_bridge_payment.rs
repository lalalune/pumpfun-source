use anchor_lang::prelude::*; use anchor_spl::{associated_token::AssociatedToken,token::{Mint,Token,TokenAccount}}; use crate::anchor_framework::*;
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
#[event_cpi]
#[derive(Accounts)]
#[instruction(source_id:[u8;32],source_commitment:[u8;32],payment_id:[u8;32],config_id:[u8;32])]
pub struct AdmitBridgePaymentV1<'info> {
 #[account(init,payer=signer,space=8,seeds=[b"bridge_source_v1",source_id.as_ref()],bump)]
 pub source_marker:Account<'info,BridgeSourceV1>,
 #[account(init,payer=signer,space=8,seeds=[b"bridge_payment_v1",payment_id.as_ref()],bump)]
 pub payment_marker:Account<'info,BridgePaymentV1>,
 /// CHECK: PDA receiver, one per source id; signs the donation transfer.
 #[account(seeds=[b"bridge_receiver_v1",source_id.as_ref()],bump)]
 pub receiver:UncheckedAccount<'info>,
 #[account(mut,associated_token::mint=mint,associated_token::authority=receiver,associated_token::token_program=token_program)]
 pub receiver_token_account:Account<'info,TokenAccount>,
 #[account(seeds=[b"epoch_tracker_v1",config_id.as_ref(),mint.key().as_ref()],bump,init_if_needed,payer=signer,space=90)]
 pub epoch_tracker:Account<'info,EpochTrackerV1>,
 #[account(seeds=[b"debouncer_v1",config_id.as_ref(),mint.key().as_ref()],bump,init_if_needed,payer=signer,space=82)]
 pub debouncer:Account<'info,DebouncerV1>,
 #[account(init_if_needed,payer=signer,associated_token::mint=mint,associated_token::authority=debouncer,associated_token::token_program=token_program)]
 pub debouncer_token_account:Account<'info,TokenAccount>,
 #[account(address=Pubkey::new_from_array(crate::codec::constants::SETTLEMENT))]
 pub mint:Account<'info,Mint>,
 #[account(mut)]
 pub signer:Signer<'info>,
 pub token_program:Program<'info,Token>,
 pub associated_token_program:Program<'info,AssociatedToken>,
 pub system_program:Program<'info,System>,
}
