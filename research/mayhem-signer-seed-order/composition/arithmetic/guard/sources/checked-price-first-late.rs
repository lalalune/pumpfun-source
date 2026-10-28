use anchor_lang::prelude::*;

#[repr(C)]
pub struct SellEvent {
 pub sol_vault: Pubkey,
 pub mint: Pubkey,
 pub sol_amount: u64,
 pub token_amount: u64,
 pub sol_vault_balance: u64,
 pub token_vault_balance: u64,
 pub state_sol_deployed: i128,
 pub state_token_net: i128,
 pub virtual_sol: u64,
 pub virtual_tokens: u64,
 pub global_sol_deployed: i128,
 pub timestamp: i64,
 pub end_timestamp: i64,
 pub real_sol: u64,
 pub real_tokens: u64,
 pub quote_amount: u64,
 pub quote_vault_balance: u64,
 pub state_quote_deployed: i128,
 pub virtual_quote: u64,
 pub global_quote_deployed: i128,
 pub real_quote: u64,
 pub quote_mint: Pubkey,
 pub version: u32,
 pub retained_reserve_bps: u16,
 pub side: u8,
}

impl AnchorSerialize for SellEvent {
 fn serialize<W: std::io::Write>(&self, writer:&mut W)->std::io::Result<()> {
  writer.write_all(&[self.side])?;
  AnchorSerialize::serialize(&self.sol_vault, writer)?;
  AnchorSerialize::serialize(&self.mint, writer)?;
  AnchorSerialize::serialize(&self.sol_amount, writer)?;
  AnchorSerialize::serialize(&self.token_amount, writer)?;
  AnchorSerialize::serialize(&self.sol_vault_balance, writer)?;
  AnchorSerialize::serialize(&self.token_vault_balance, writer)?;
  AnchorSerialize::serialize(&self.state_sol_deployed, writer)?;
  AnchorSerialize::serialize(&self.state_token_net, writer)?;
  AnchorSerialize::serialize(&self.virtual_sol, writer)?;
  AnchorSerialize::serialize(&self.virtual_tokens, writer)?;
  AnchorSerialize::serialize(&self.global_sol_deployed, writer)?;
  AnchorSerialize::serialize(&self.timestamp, writer)?;
  AnchorSerialize::serialize(&self.end_timestamp, writer)?;
  AnchorSerialize::serialize(&self.real_sol, writer)?;
  AnchorSerialize::serialize(&self.real_tokens, writer)?;
  AnchorSerialize::serialize(&self.version, writer)?;
  AnchorSerialize::serialize(&self.retained_reserve_bps, writer)?;
  AnchorSerialize::serialize(&self.quote_amount, writer)?;
  AnchorSerialize::serialize(&self.quote_vault_balance, writer)?;
  AnchorSerialize::serialize(&self.state_quote_deployed, writer)?;
  AnchorSerialize::serialize(&self.virtual_quote, writer)?;
  AnchorSerialize::serialize(&self.global_quote_deployed, writer)?;
  AnchorSerialize::serialize(&self.real_quote, writer)?;
  AnchorSerialize::serialize(&self.quote_mint, writer)?;
  Ok(())
 }
}
impl AnchorDeserialize for SellEvent {
 fn deserialize_reader<R: std::io::Read>(reader:&mut R)->std::io::Result<Self> {
  let side=AnchorDeserialize::deserialize_reader(reader)?;
  let sol_vault=AnchorDeserialize::deserialize_reader(reader)?;
  let mint=AnchorDeserialize::deserialize_reader(reader)?;
  let sol_amount=AnchorDeserialize::deserialize_reader(reader)?;
  let token_amount=AnchorDeserialize::deserialize_reader(reader)?;
  let sol_vault_balance=AnchorDeserialize::deserialize_reader(reader)?;
  let token_vault_balance=AnchorDeserialize::deserialize_reader(reader)?;
  let state_sol_deployed=AnchorDeserialize::deserialize_reader(reader)?;
  let state_token_net=AnchorDeserialize::deserialize_reader(reader)?;
  let virtual_sol=AnchorDeserialize::deserialize_reader(reader)?;
  let virtual_tokens=AnchorDeserialize::deserialize_reader(reader)?;
  let global_sol_deployed=AnchorDeserialize::deserialize_reader(reader)?;
  let timestamp=AnchorDeserialize::deserialize_reader(reader)?;
  let end_timestamp=AnchorDeserialize::deserialize_reader(reader)?;
  let real_sol=AnchorDeserialize::deserialize_reader(reader)?;
  let real_tokens=AnchorDeserialize::deserialize_reader(reader)?;
  let version=AnchorDeserialize::deserialize_reader(reader)?;
  let retained_reserve_bps=AnchorDeserialize::deserialize_reader(reader)?;
  let quote_amount=AnchorDeserialize::deserialize_reader(reader)?;
  let quote_vault_balance=AnchorDeserialize::deserialize_reader(reader)?;
  let state_quote_deployed=AnchorDeserialize::deserialize_reader(reader)?;
  let virtual_quote=AnchorDeserialize::deserialize_reader(reader)?;
  let global_quote_deployed=AnchorDeserialize::deserialize_reader(reader)?;
  let real_quote=AnchorDeserialize::deserialize_reader(reader)?;
  let quote_mint=AnchorDeserialize::deserialize_reader(reader)?;
  Ok(Self { side,sol_vault,mint,sol_amount,token_amount,sol_vault_balance,token_vault_balance,state_sol_deployed,state_token_net,virtual_sol,virtual_tokens,global_sol_deployed,timestamp,end_timestamp,real_sol,real_tokens,version,retained_reserve_bps,quote_amount,quote_vault_balance,state_quote_deployed,virtual_quote,global_quote_deployed,real_quote,quote_mint })
 }
}
impl Discriminator for SellEvent { const DISCRIMINATOR: &'static [u8]=&[0x31,0x48,0x7b,0x2d,0x6e,0x40,0xb0,0x85]; }





































































































impl anchor_lang::Event for SellEvent {
 fn data(&self)->Vec<u8> {
  let mut data =
Vec::with_capacity(256);
  data.extend_from_slice(Self::DISCRIMINATOR); self.serialize(&mut data).unwrap(); data
 }
}
use super::sell::{LegacySell,SellCurve}; use super::buy::{LegacyBuy,clone_info,BuyError};
use crate::MayhemError;









































































pub fn legacy_buy_handler(ctx:Context<LegacyBuy>,reference:u128,tolerance_bps:u16,retained_reserve_bps:u16)->Result<()> {
 let a=&mut *ctx.accounts;
 a.mayhem_state.validate_trade(&a.global_params)?;





 a.mayhem_state.validate_quote(a.bonding_curve.real_sol_reserves,&a.global_params,&Pubkey::default())?;





 let c=&a.bonding_curve;

 let price_check:std::result::Result<(),MayhemError> = (|| {
 let vt=c.virtual_token_reserves as u128;if vt==0{return Err(MayhemError::MathOverflow);}
 let scaled=reference.checked_mul(tolerance_bps as u128);
 let vs=c.virtual_sol_reserves as u128;let price=vs*1_000_000_000_000_000u128/vt;
 let delta=scaled.ok_or(MayhemError::MathOverflow)?/10_000;
 let low=reference.checked_sub(delta).ok_or(MayhemError::MathOverflow)?;
 let high=reference.checked_add(delta).ok_or(MayhemError::MathOverflow)?;
 if price<low||price>high{return Err(MayhemError::PumpCpiSlippage);}
 Ok(())
 })();price_check?;let vt=c.virtual_token_reserves as u128;let vs=c.virtual_sol_reserves as u128;
 let retained=crate::state::retained_basis_points(retained_reserve_bps);
 let (input,output)=crate::state::buy_amounts(vt,vs,c.real_sol_reserves,c.real_token_reserves,a.mayhem_token_vault.amount as u128,a.global_params.field_2,retained);
 let before_sol=a.sol_vault.lamports();let before_tokens=a.mayhem_token_vault.amount;
 let cpi_program=a.pump_program.key();
 let bump=[ctx.bumps.sol_vault];let seeds:&[&[u8]]=&[b"sol-vault",&bump];
 let signer_seeds=&[seeds];
 let mut cpi_ctx=CpiContext::new_with_signer(cpi_program,crate::pump::cpi::accounts::Buy {global:clone_info(a.global.as_ref()),fee_recipient:clone_info(a.fee_recipient.as_ref()),mint:clone_info(a.mint.as_ref().as_ref()),bonding_curve:clone_info(a.bonding_curve.as_ref().as_ref()),associated_bonding_curve:clone_info(a.associated_bonding_curve.as_ref().as_ref()),associated_user:clone_info(a.mayhem_token_vault.as_ref().as_ref()),user:clone_info(a.sol_vault.as_ref()),system_program:clone_info(a.system_program.as_ref()),token_program:clone_info(a.token_program.as_ref()),creator_vault:clone_info(a.creator_vault.as_ref()),event_authority:clone_info(a.pump_event_authority.as_ref()),program:clone_info(a.pump_program.as_ref()),global_volume_accumulator:clone_info(a.global_volume_accumulator.as_ref()),user_volume_accumulator:clone_info(a.user_volume_accumulator.as_ref()),fee_config:clone_info(a.fee_config.as_ref()),fee_program:clone_info(a.fee_program.as_ref())},signer_seeds);
 cpi_ctx.remaining_accounts=vec![clone_info(a.bonding_curve_v2.as_ref()),clone_info(a.buyback_recipient.as_ref())];
 crate::pump::cpi::buy(cpi_ctx,input,output,false).map_err(|_| {


    error!(BuyError::PumpCpiFailed)
 })?;

 a.mayhem_token_vault.reload()?;a.bonding_curve.reload()?;




              let sol=before_sol-a.sol_vault.lamports();
              let tokens=a.mayhem_token_vault.amount-before_tokens;
 crate::state::record_amm_buy(&mut a.global_params,&mut a.mayhem_state,sol,tokens,&Pubkey::default())?;






 let event=SellEvent{side:0,sol_vault:a.sol_vault.key(),mint:a.mint.key(),sol_amount:sol,token_amount:tokens,sol_vault_balance:a.sol_vault.lamports(),token_vault_balance:a.mayhem_token_vault.amount,state_sol_deployed:a.mayhem_state.field_56,state_token_net:a.mayhem_state.field_72,virtual_sol:a.bonding_curve.virtual_sol_reserves,virtual_tokens:a.bonding_curve.virtual_token_reserves,global_sol_deployed:a.global_params.sol_deployed,timestamp:Clock::get()?.unix_timestamp,end_timestamp:a.mayhem_state.end_timestamp,real_sol:a.bonding_curve.real_sol_reserves,real_tokens:a.bonding_curve.real_token_reserves,version:a.global_params.version,retained_reserve_bps,quote_amount:sol,quote_vault_balance:a.sol_vault.lamports(),state_quote_deployed:a.mayhem_state.field_56,virtual_quote:a.bonding_curve.virtual_sol_reserves,global_quote_deployed:a.global_params.sol_deployed,real_quote:a.bonding_curve.real_sol_reserves,quote_mint:Pubkey::default()};
 emit!(event);emit_cpi!(event);Ok(())
}


































































pub fn legacy_sell_handler(ctx:Context<LegacySell>,reference:u128,tolerance_bps:u16,retained_reserve_bps:u16)->Result<()> {
 let a=&mut *ctx.accounts;
 a.mayhem_state.validate_trade(&a.global_params)?;
 a.mayhem_state.validate_quote(a.bonding_curve.real_sol_reserves, &a.global_params, &Pubkey::default())?;




 let c=&a.bonding_curve;
 legacy_price_check(c.virtual_token_reserves as u128,c.virtual_sol_reserves as u128,reference,tolerance_bps)?;
 let (input, minimum) = crate::state::sell_amounts(c.virtual_token_reserves,c.virtual_sol_reserves,c.real_sol_reserves,a.mayhem_token_vault.amount,a.global_params.field_2,retained_reserve_bps);







 let before_sol=a.sol_vault.lamports();let before_tokens=a.mayhem_token_vault.amount;


 crate::pump::cpi::sell(CpiContext::new_with_signer(a.pump_program.key(),crate::pump::cpi::accounts::Sell {
  global:clone_sell_info(a.global.as_ref()),
  fee_recipient:clone_sell_info(a.fee_recipient.as_ref()),
  mint:clone_sell_info(a.mint.as_ref().as_ref()),
  bonding_curve:clone_sell_info(a.bonding_curve.as_ref().as_ref()),
  associated_bonding_curve:clone_sell_info(a.associated_bonding_curve.as_ref().as_ref()),
  associated_user:clone_sell_info(a.mayhem_token_vault.as_ref().as_ref()),
  user:clone_sell_info(a.sol_vault.as_ref()),
  system_program:clone_sell_info(a.system_program.as_ref()),
  creator_vault:clone_sell_info(a.creator_vault.as_ref()),
  token_program:clone_sell_info(a.token_program.as_ref()),
  event_authority:clone_sell_info(a.pump_event_authority.as_ref()),
  program:clone_sell_info(a.pump_program.as_ref()),
  fee_config:clone_sell_info(a.fee_config.as_ref()),
  fee_program:clone_sell_info(a.fee_program.as_ref()),
 },&[&[b"sol-vault", &[ctx.bumps.sol_vault]]])
  .with_remaining_accounts(vec![clone_sell_info(a.bonding_curve_v2.as_ref()),clone_sell_info(a.buyback_recipient.as_ref())]),input,minimum).map_err(|_|error!(MayhemError::PumpCpiFailed))?;
 a.mayhem_token_vault.reload()?;a.bonding_curve.reload()?;






    let sol=          a.sol_vault.lamports()-before_sol;
    let tokens=          before_tokens-a.mayhem_token_vault.amount;
 crate::state::record_sell(&mut a.global_params,&mut a.mayhem_state,sol,tokens,&Pubkey::default())?;


 let event=SellEvent{side:1,sol_vault:a.sol_vault.key(),mint:a.mint.key(),sol_amount:sol,token_amount:tokens,sol_vault_balance:a.sol_vault.lamports(),token_vault_balance:a.mayhem_token_vault.amount,state_sol_deployed:a.mayhem_state.field_56,state_token_net:a.mayhem_state.field_72,virtual_sol:a.bonding_curve.virtual_sol_reserves,virtual_tokens:a.bonding_curve.virtual_token_reserves,global_sol_deployed:a.global_params.sol_deployed,timestamp:Clock::get()?.unix_timestamp,end_timestamp:a.mayhem_state.end_timestamp,real_sol:a.bonding_curve.real_sol_reserves,real_tokens:a.bonding_curve.real_token_reserves,version:a.global_params.version,retained_reserve_bps,quote_amount:sol,quote_vault_balance:a.sol_vault.lamports(),state_quote_deployed:a.mayhem_state.field_56,virtual_quote:a.bonding_curve.virtual_sol_reserves,global_quote_deployed:a.global_params.sol_deployed,real_quote:a.bonding_curve.real_sol_reserves,quote_mint:Pubkey::default()};
 emit!(event);emit_cpi!(event);Ok(())
}

#[inline(always)]
fn clone_sell_info<'a>(info:&AccountInfo<'a>)->AccountInfo<'a> {
 AccountInfo { key:info.key, lamports:std::rc::Rc::clone(&info.lamports), data:std::rc::Rc::clone(&info.data), owner:info.owner, _unused:info._unused, is_signer:info.is_signer, is_writable:info.is_writable, executable:info.executable }
}

#[inline(always)]
fn legacy_price_check(vt:u128,vs:u128,reference:u128,tolerance_bps:u16)->core::result::Result<(),MayhemError> {

  if vt==0{return Err(MayhemError::MathOverflow);}
  let price=vs*1_000_000_000_000_000u128/vt;
  let scaled=reference.checked_mul(tolerance_bps as u128);
  let delta=scaled.ok_or(MayhemError::MathOverflow)?/10_000;
  let low=reference.checked_sub(delta).ok_or(MayhemError::MathOverflow)?;
  let high=reference.checked_add(delta).ok_or(MayhemError::MathOverflow)?;
  if price<low||price>high{return Err(MayhemError::PumpCpiSlippage);}
  Ok(())
}
