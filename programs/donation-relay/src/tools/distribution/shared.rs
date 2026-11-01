use crate::tools::fair_distribution::fair_amounts;
use anchor_lang::prelude::*;
use anchor_spl::token_interface::{TokenAccount,TransferChecked};
use crate::anchor_framework::{Share,Receipt};
use crate::business_error_codes::ErrorCode as Code;
macro_rules! worker_error {($code:ident,$line:literal)=>{anchor_lang::error::Error::from(anchor_lang::error::AnchorError {
 error_name:Code::$code.name(),error_code_number:Code::$code.into(),error_msg:Code::$code.to_string(),
 error_origin:Some(anchor_lang::error::ErrorOrigin::Source(anchor_lang::error::Source {filename:"programs/contracts/src/tools/distribution/shared.rs",line:$line})),compared_values:None})};}
pub struct DistributionContext<'a,'info> {pub remaining:&'a [AccountInfo<'info>],pub source:AccountInfo<'info>,pub mint:AccountInfo<'info>,pub program:AccountInfo<'info>,pub authority:AccountInfo<'info>}
pub struct DistributionArgs<'a,'b,'c> {pub shares:&'a [Share],pub total:u64,pub decimals:u8,pub seeds:&'a [&'b [&'c [u8]]],pub expected_program:Pubkey}
pub fn distribute<'info>(ctx:DistributionContext<'info,'info>,args:DistributionArgs)->Result<Vec<Receipt>> {
 let shares=args.shares;let total=args.total;let decimals=args.decimals;let expected_program=args.expected_program;let seeds=args.seeds;
 if ctx.program.key()!=expected_program {return Err(worker_error!(InvalidTokenAccountProgram,82).with_pubkeys((ctx.program.key(),expected_program)));}
 if ctx.remaining.len()<shares.len() {return Err(Code::InsufficientRemainingAccounts.into());}
 let weights:Vec<u16>=shares.iter().map(|share|share.bps).collect();
 let amounts=fair_amounts(total,&weights)?;
 transfer_shares(&ctx,shares.iter().zip(amounts.iter()),decimals,expected_program,seeds)?;
 Ok(shares.iter().zip(amounts.iter()).map(|(share,amount)|Receipt {share_type:share.share_type.clone(),address:share.address,amount:*amount,bps:share.bps}).collect())
}

#[inline(never)]
fn transfer_shares<'info>(ctx:&DistributionContext<'info,'info>,rows:core::iter::Zip<core::slice::Iter<'_,Share>,core::slice::Iter<'_,u64>>,decimals:u8,expected_program:Pubkey,seeds:&[&[&[u8]]])->Result<()> {
 let mint_key=ctx.mint.key;
 for (info,(share,amount)) in ctx.remaining.iter().zip(rows) {
  let token=InterfaceAccount::<TokenAccount>::try_from(info)?;
  if token.owner!=share.address {return Err(worker_error!(InvalidTokenAccountOwner,191).with_pubkeys((token.owner,share.address)));}
  if token.mint!=*mint_key {return Err(worker_error!(InvalidTokenAccountMint,196).with_pubkeys((token.mint,*mint_key)));}
  if *info.owner!=expected_program {return Err(worker_error!(InvalidTokenAccountProgram,201).with_pubkeys((*info.owner,expected_program)));}
  if *amount!=0 {anchor_spl::token_interface::transfer_checked(CpiContext::new_with_signer(ctx.program.clone(),TransferChecked {from:ctx.source.clone(),mint:ctx.mint.clone(),to:info.clone(),authority:ctx.authority.clone()},seeds),*amount,decimals)?;}
 }
 Ok(())
}

pub fn distribute_exact<'info>(ctx:DistributionContext<'info,'info>,transfers:&[crate::anchor_framework::ExactTransfer],seeds:&[&[&[u8]]],total:u64,expected_program:Pubkey,decimals:u8)->Result<()> {
 let DistributionContext {remaining,source,mint,program,authority}=ctx;
 if total==0 {return Err(worker_error!(InvalidBalance,142));}
 if transfers.is_empty() || remaining.len()!=transfers.len() {return Err(worker_error!(InvalidInstructionDataLength,131));}
 let mut sum:u64=0;
 for row in transfers.iter() {sum=sum.checked_add(row.amount).ok_or(Code::ArithmeticOverflow)?;}
 if sum!=total {return Err(worker_error!(InputAmountMismatch,170));}
 if program.key()!=expected_program {return Err(worker_error!(InvalidTokenAccountProgram,149).with_pubkeys((program.key(),expected_program)));}
 let mint_key=mint.key();
 for (index,row) in transfers.iter().enumerate() {
  let info=&remaining[index];
  let token=InterfaceAccount::<TokenAccount>::try_from(info)?;
  if token.owner!=row.address {return Err(worker_error!(InvalidTokenAccountOwner,191).with_pubkeys((token.owner,row.address)));}
  if token.mint!=mint_key {return Err(worker_error!(InvalidTokenAccountMint,196).with_pubkeys((token.mint,mint_key)));}
  if *token.to_account_info().owner!=expected_program {return Err(worker_error!(InvalidTokenAccountProgram,201).with_pubkeys((*token.to_account_info().owner,expected_program)));}
  if row.amount!=0 {anchor_spl::token_interface::transfer_checked(CpiContext::new_with_signer(program.clone(),TransferChecked {from:source.clone(),mint:mint.clone(),to:info.clone(),authority:authority.clone()},seeds),row.amount,decimals)?;}
 }
 Ok(())
}

pub struct BurnCloseContext<'info> {pub token:AccountInfo<'info>,pub mint:AccountInfo<'info>,pub authority:AccountInfo<'info>,pub destination:AccountInfo<'info>,pub program:AccountInfo<'info>}
pub fn burn_and_close<'info>(ctx:BurnCloseContext<'info>,amount:u64,seeds:&[&[&[u8]]])->Result<()> {
 let BurnCloseContext {token,mint,authority,destination,program}=ctx;
 if amount!=0 {anchor_spl::token_interface::burn(CpiContext::new_with_signer(program.clone(),anchor_spl::token_interface::Burn {mint:mint,from:token.clone(),authority:authority.clone()},seeds),amount)?;}
 anchor_spl::token_interface::close_account(CpiContext::new_with_signer(program,anchor_spl::token_interface::CloseAccount {account:token,destination:destination,authority:authority},seeds))?;Ok(())
}


impl<'a,'b,'c> DistributionArgs<'a,'b,'c> {
 pub fn new(shares:&'a [Share],seeds:&'a [&'b [&'c [u8]]],total:u64,expected_program:&Pubkey,decimals:u8)->Self {Self {shares,seeds,total,expected_program:*expected_program,decimals}}
}
