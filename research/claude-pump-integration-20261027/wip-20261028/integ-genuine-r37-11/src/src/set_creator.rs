use anchor_lang::prelude::*;
use crate::{Global,PumpError,trade_types::BondingCurve};
pub const METAPLEX:Pubkey=anchor_lang::solana_program::pubkey!("metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s");
use anchor_spl::metadata::MetadataAccount as CreatorMetadata;
#[event_cpi]
#[derive(Accounts)]pub struct SetCreator<'info>{
 pub set_creator_authority:Signer<'info>,
 #[account(seeds=[b"global"],bump,has_one=set_creator_authority @ PumpError::NotAuthorized)]pub global:Account<'info,Global>,
 pub mint:Account<'info,anchor_spl::token::Mint>,
 #[account(seeds=[b"metadata",METAPLEX.as_ref(),mint.key().as_ref()],bump,seeds::program=METAPLEX)]pub metadata:Account<'info,CreatorMetadata>,
 #[account(mut,seeds=[b"bonding-curve",mint.key().as_ref()],bump)]pub bonding_curve:Account<'info,BondingCurve>,
}
#[event_cpi]
#[derive(Accounts)]pub struct SetMetaplexCreator<'info>{
 pub mint:Account<'info,anchor_spl::token::Mint>,
 #[account(seeds=[b"metadata",METAPLEX.as_ref(),mint.key().as_ref()],bump,seeds::program=METAPLEX)]pub metadata:Account<'info,CreatorMetadata>,
 #[account(mut,seeds=[b"bonding-curve",mint.key().as_ref()],bump)]pub bonding_curve:Account<'info,BondingCurve>,
}
#[event]#[derive(Clone)]pub struct SetCreatorEvent{pub timestamp:i64,pub mint:Pubkey,pub bonding_curve:Pubkey,pub creator:Pubkey}
#[event]#[derive(Clone)]pub struct SetMetaplexCreatorEvent{pub timestamp:i64,pub mint:Pubkey,pub bonding_curve:Pubkey,pub metadata:Pubkey,pub creator:Pubkey}
pub fn set(mut ctx:Context<SetCreator>,creator:Pubkey)->Result<()>{let a=&mut ctx.accounts;if a.bonding_curve.creator!=Pubkey::default(){msg!("Bonding curve has creator already set");return Ok(());}if let Some(cs)=&a.metadata.creators{let creator=cs[0].address;a.bonding_curve.creator=creator;let e=SetMetaplexCreatorEvent{timestamp:Clock::get()?.unix_timestamp,mint:a.mint.key(),bonding_curve:a.bonding_curve.key(),metadata:a.metadata.key(),creator};emit!(e.clone());emit_cpi!(e);}else{a.bonding_curve.creator=creator;let e=SetCreatorEvent{timestamp:Clock::get()?.unix_timestamp,mint:a.mint.key(),bonding_curve:a.bonding_curve.key(),creator};emit!(e.clone());emit_cpi!(e);}Ok(())}
pub fn sync(mut ctx:Context<SetMetaplexCreator>)->Result<()>{let a=&mut ctx.accounts;if a.bonding_curve.creator!=Pubkey::default(){msg!("Bonding curve has creator already set");return Ok(());}if let Some(cs)=&a.metadata.creators{let creator=cs[0].address;a.bonding_curve.creator=creator;let e=SetMetaplexCreatorEvent{timestamp:Clock::get()?.unix_timestamp,mint:a.mint.key(),bonding_curve:a.bonding_curve.key(),metadata:a.metadata.key(),creator};emit!(e.clone());emit_cpi!(e);}else{msg!("Missing metaplex creators");}Ok(())}
