#[path = "fee_recipient.rs"]
pub(crate) mod fee_recipient;
use anchor_lang::prelude::*;
use anchor_spl::token_interface::{self,Mint,TokenAccount,TokenInterface,TransferChecked};
use crate::{Global,PumpError};
use crate::trade_types::{BondingCurve,TradeEvent};

#[derive(Clone)]pub struct LegacyCurve(pub BondingCurve,pub usize);
impl std::ops::Deref for LegacyCurve{type Target=BondingCurve;fn deref(&self)->&BondingCurve{&self.0}}
impl std::ops::DerefMut for LegacyCurve{fn deref_mut(&mut self)->&mut BondingCurve{&mut self.0}}
impl Owner for LegacyCurve{fn owner()->Pubkey{crate::ID}}
impl AccountDeserialize for LegacyCurve{fn try_deserialize(buf:&mut &[u8])->Result<Self>{let len=buf.len();Ok(Self(BondingCurve::try_deserialize(buf)?,len))}fn try_deserialize_unchecked(buf:&mut &[u8])->Result<Self>{Self::try_deserialize(buf)}}
impl AccountSerialize for LegacyCurve{fn try_serialize<W:std::io::Write>(&self,w:&mut W)->Result<()>{let mut b=Vec::new();self.0.try_serialize(&mut b)?;w.write_all(&b[..self.1.min(b.len())])?;Ok(())}}
pub use crate::pump_fees::{
    accounts::FeeConfig as LegacyFeeConfig,
    program::PumpFees as LegacyFeesProgram,
};

#[derive(Accounts)]
pub struct LegacySell<'info>{
 #[account(seeds=[b"global"],bump)]pub global:Box<Account<'info,Global>>,
 /// CHECK: handler validates recipient.
 #[account(mut)]pub fee_recipient:UncheckedAccount<'info>,
 pub mint:InterfaceAccount<'info,Mint>,
 #[account(mut,seeds=[b"bonding-curve",mint.key().as_ref()],bump,constraint=bonding_curve.quote_mint==Pubkey::default() @ PumpError::UnsupportedQuoteMint)]pub bonding_curve:Account<'info,BondingCurve>,
 #[account(mut,associated_token::mint=mint,associated_token::authority=bonding_curve,associated_token::token_program=token_program)]pub associated_bonding_curve:InterfaceAccount<'info,TokenAccount>,
 #[account(mut,token::mint=mint)]pub associated_user:InterfaceAccount<'info,TokenAccount>,
 #[account(mut)]pub user:Signer<'info>,
 pub system_program:Program<'info,System>,
 /// CHECK: PDA checked.
 #[account(mut,seeds=[b"creator-vault",bonding_curve.creator.as_ref()],bump)]pub creator_vault:AccountInfo<'info>,
 pub token_program:Interface<'info,TokenInterface>,
 /// CHECK: event authority.
 #[account(seeds=[b"__event_authority"],bump)]pub event_authority:AccountInfo<'info>,
 /// CHECK: self CPI.
 pub program:Program<'info,crate::program::PumpRecovered>,
 /// CHECK: fee program validates config.
 #[account(seeds=[b"fee_config",crate::ID.as_ref()],bump,seeds::program=fee_program.key())]
 pub fee_config:Account<'info,LegacyFeeConfig>,
 /// CHECK: canonical dependency.
 pub fee_program:Program<'info,LegacyFeesProgram>,
}
fn add(a:u64,b:u64)->Result<u64>{a.checked_add(b).ok_or_else(||error!(PumpError::Overflow))}
fn sub(a:u64,b:u64)->Result<u64>{a.checked_sub(b).ok_or_else(||error!(PumpError::Overflow))}
fn narrow(a:u128)->Result<u64>{u64::try_from(a).map_err(|_|error!(PumpError::Truncation))}
pub fn execute(ctx:Context<LegacySell>,amount:u64,minimum:u64)->Result<()>{
 let a=&mut *ctx.accounts;
 crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.user)?;

let c=&a.bonding_curve;
 crate::legacy_sell::fee_recipient::validate_fee_recipient(&a.fee_recipient,&a.global,&a.bonding_curve)?;
 require!(!c.complete,PumpError::BondingCurveComplete);require_gt!(amount,0,PumpError::SellZeroAmount);require_gte!(a.associated_user.amount,amount,PumpError::NotEnoughTokensToSell);
 let quote=narrow(amount as u128*c.virtual_quote_reserves as u128/(c.virtual_token_reserves as u128+amount as u128))?;
 let (initial_protocol_fee,initial_creator_fee,protocol_fee_bps,creator_fee_bps)={let values=crate::legacy_sell::fee_cpi::trade_fees(
  &a.global,&a.bonding_curve,&a.mint,&a.fee_config,&a.fee_program,a.program.as_ref(),quote
 )?;if a.user.key()==a.global.whitelist_pda{(0,0,0,0)}else{values}};
 let cb=if c.creator==Pubkey::default(){0}else{creator_fee_bps};let pf=initial_protocol_fee;let cf=initial_creator_fee;let output=sub(sub(quote,pf)?,cf)?;require_gte!(output,minimum,PumpError::TooLittleSolReceived);
 let vb=add(c.virtual_token_reserves,amount)?;let vq=sub(c.virtual_quote_reserves,quote)?;let rb=add(c.real_token_reserves,amount)?;let rq=sub(c.real_quote_reserves,quote)?;
 token_interface::transfer_checked(CpiContext::new(a.token_program.to_account_info(),TransferChecked{from:a.associated_user.to_account_info(),mint:a.mint.to_account_info(),to:a.associated_bonding_curve.to_account_info(),authority:a.user.to_account_info()}),amount,a.mint.decimals)?;
 let rem=ctx.remaining_accounts;let index=if c.is_cashback_coin {let acc=rem.first().ok_or_else(||error!(PumpError::MissingCashbackAccounts))?;require!(acc.key()==Pubkey::find_program_address(&[b"user_volume_accumulator",a.user.key().as_ref()],&crate::ID).0&&acc.owner==&crate::ID&&acc.data_len()>=82,PumpError::InvalidCashbackAccumulator);1}else{0};
 let v2=rem.get(index).ok_or_else(||error!(PumpError::InvalidBondingCurveV2))?;require!(v2.key()==Pubkey::find_program_address(&[b"bonding-curve-v2",a.mint.key().as_ref()],&crate::ID).0,PumpError::InvalidBondingCurveV2);
 let bbps=if c.is_mayhem_mode{0}else{a.global.buyback_basis_points};
 let cashback_coin=c.is_cashback_coin;
 if cf!=0 && !cashback_coin {crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.user,&a.creator_vault)?;}
 if cf!=0 {a.bonding_curve.sub_lamports(cf)?;if cashback_coin{rem[0].add_lamports(cf)?;let mut d=rem[0].try_borrow_mut_data()?;let n=u64::from_le_bytes(d[74..82].try_into().unwrap());d[74..82].copy_from_slice(&add(n,cf)?.to_le_bytes());}else{a.creator_vault.add_lamports(cf)?;}}
 let bb=rem.get(index+1).ok_or_else(||error!(PumpError::BuybackFeeRecipientMissing))?;require!(a.global.buyback_fee_recipients.contains(bb.key),PumpError::BuybackFeeRecipientNotAuthorized);
 if output!=0 {a.bonding_curve.sub_lamports(output)?;a.user.add_lamports(output)?;}
 let (bf,protocol_fee)=crate::buy_v2::recipient_payments::split_protocol_fee(&a.global,pf,c.is_mayhem_mode);
 if bf!=0 {a.bonding_curve.sub_lamports(bf)?;bb.add_lamports(bf)?;}
 if protocol_fee!=0 {a.bonding_curve.sub_lamports(protocol_fee)?;a.fee_recipient.add_lamports(protocol_fee)?;}
 let ev=TradeEvent{mint:a.mint.key(),sol_amount:quote,token_amount:amount,is_buy:false,user:a.user.key(),timestamp:Clock::get()?.unix_timestamp,virtual_sol_reserves:vq,virtual_token_reserves:vb,real_sol_reserves:rq,real_token_reserves:rb,fee_recipient:a.fee_recipient.key(),fee_basis_points:protocol_fee_bps,fee:pf,creator:c.creator,creator_fee_basis_points:if c.is_cashback_coin{0}else{creator_fee_bps},creator_fee:if c.is_cashback_coin{0}else{cf},track_volume:false,total_unclaimed_tokens:0,total_claimed_tokens:0,current_sol_volume:0,last_update_timestamp:0,ix_name:"sell".into(),mayhem_mode:c.is_mayhem_mode,cashback_fee_basis_points:if c.is_cashback_coin{cb}else{0},cashback:if c.is_cashback_coin{cf}else{0},buyback_fee_basis_points:bbps,buyback_fee:bf,shareholders:vec![],quote_mint:Pubkey::default(),quote_amount:quote,virtual_quote_reserves:vq,real_quote_reserves:rq,holder_rewards_bps:if c.is_holder_reward{cb}else{0},holder_rewards:if c.is_holder_reward{cf}else{0},creator_fee_unclaimed:c.creator_fee,unparsed_trailing_field:0};
 let c=&mut a.bonding_curve;c.virtual_token_reserves=vb;c.virtual_quote_reserves=vq;c.real_token_reserves=rb;c.real_quote_reserves=rq;emit!(ev.clone());emit_cpi!(ev);Ok(())
}

#[path="fee_cpi.rs"]
pub(crate) mod fee_cpi;

#[path="util/fee.rs"]
pub mod fee_math;
