use anchor_lang::prelude::*;
use crate::{Global,PumpError};
#[event_cpi]
#[derive(Accounts)]
pub struct SetParams<'info>{
 #[account(mut,seeds=[b"global"],bump,has_one=authority @ PumpError::NotAuthorized)]pub global:Account<'info,Global>,
 #[account(mut)]pub authority:Signer<'info>,
}
pub use crate::SetParamsEvent;


