use crate::*;
use crate::trade::native_transfer_fee::Fee;

#[inline(never)]
pub fn calculate_fee(fee:&Option<Fee>,amount:u64)->Result<u64>{
 match *fee {
  None=>Ok(0),
  Some(fee)=>fee.calculate_fee(amount).ok_or_else(||error!(PumpError::Overflow)),
 }
}

#[inline(never)]
pub fn post_fee_amount(fee:&Option<Fee>,amount:u64)->Result<u64>{
 let fee=calculate_fee(fee,amount)?;
 amount.checked_sub(fee).ok_or_else(||error!(PumpError::Overflow))
}

#[inline(never)]
pub fn pre_fee_amount(fee:&Option<Fee>,amount:u64)->Result<u64>{
 match *fee {
  None=>Ok(amount),
  Some(fee)=>fee.calculate_pre_fee_amount(amount).ok_or_else(||error!(PumpError::Overflow)),
 }
}
