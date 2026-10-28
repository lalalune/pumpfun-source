use crate::*;
use crate::trade::native_transfer_fee::Fee;

#[inline(never)]
pub fn calculate_fee(fee:&Option<Fee>,amount:u64)->Result<u64>{
 match *fee {
  None=>Ok(0),
// layout-pad(40): aligns the next Source site with the original line







































  Some(fee)=>fee.calculate_fee(amount).ok_or_else(||error!(PumpError::Overflow)),
 }
}

#[inline(never)]
pub fn post_fee_amount(fee:&Option<Fee>,amount:u64)->Result<u64>{
 let fee=calculate_fee(fee,amount)?;
// layout-pad(1): aligns the next Source site with the original line
 amount.checked_sub(fee).ok_or_else(||error!(PumpError::Overflow))
}

#[inline(never)]
pub fn pre_fee_amount(fee:&Option<Fee>,amount:u64)->Result<u64>{
 match *fee {
  None=>Ok(amount),
// layout-pad(3): aligns the next Source site with the original line


  Some(fee)=>fee.calculate_pre_fee_amount(amount).ok_or_else(||error!(PumpError::Overflow)),
 }
}
