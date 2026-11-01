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
#[event_cpi]
#[derive(Accounts)]
#[instruction(source_id:[u8;32],source_commitment:[u8;32],payment_id:[u8;32],amount:u64)]
pub struct RecoverBridgePaymentV1<'info> {
 #[account(init,payer=payer,space=8,seeds=[b"bridge_source_v1",source_id.as_ref()],bump)]
 pub source_marker:Account<'info,BridgeSourceV1>,
 #[account(init,payer=payer,space=8,seeds=[b"bridge_payment_v1",payment_id.as_ref()],bump)]
 pub payment_marker:Account<'info,BridgePaymentV1>,
 /// CHECK: PDA receiver, one per source id; signs the recovery transfer.
 #[account(seeds=[b"bridge_receiver_v1",source_id.as_ref()],bump)]
 pub receiver:UncheckedAccount<'info>,
 #[account(mut,associated_token::mint=mint,associated_token::authority=receiver,associated_token::token_program=token_program)]
 pub receiver_token_account:Account<'info,TokenAccount>,
 /// CHECK: owner of the destination token account.
 pub destination_owner:UncheckedAccount<'info>,
 #[account(mut,associated_token::mint=mint,associated_token::authority=destination_owner,associated_token::token_program=token_program)]
 pub destination_token_account:Account<'info,TokenAccount>,
 #[account(address=Pubkey::new_from_array(crate::codec::constants::SETTLEMENT) @ crate::business_error_codes::ErrorCode::InvalidMint)]
 pub mint:Account<'info,Mint>,
 pub program_data:Account<'info,ProgramData>,
 pub authority:Signer<'info>,
 #[account(mut)]
 pub payer:Signer<'info>,
 pub token_program:Program<'info,Token>,
 pub associated_token_program:Program<'info,AssociatedToken>,
 pub system_program:Program<'info,System>,
}
