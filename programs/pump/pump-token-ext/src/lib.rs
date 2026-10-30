//! Token-2022 mint extension helpers (separate crate: the original links them as their own object).
#[inline(never)]
pub fn quote_extensions_supported(data:&[u8],allow_token_extensions:bool)->bool {
 tlv_check(data,allow_token_extensions).is_some()
}
fn tlv_check(data:&[u8],allow_token_extensions:bool)->Option<()> {
 if data.len()==82{return Some(());}
 if data.len()<167 || data[82..165].iter().any(|&b|b!=0) || data[165]!=1{return None;}
 let tlv=&data[166..];
 let mut seen=0u64;
 let mut offset=0usize;
 loop{
  let rest=tlv.get(offset..)?;
  if rest.len()<2{return Some(())}
  let kind=u16::from_le_bytes(rest[..2].try_into().unwrap());
  if kind==0{return Some(())}
  if rest.len()<4{return None}
  let size=u16::from_le_bytes(rest[2..4].try_into().unwrap()) as usize;
  if size+4>rest.len(){return None}
  match kind{
   18|19=>{},
   1|4|6|12|14|16|25|26=>if !allow_token_extensions{return None},
   _=>return None,
  }
  let bit=1u64<<kind;
  if seen&bit!=0{return None}
  if !extension_data_valid(kind,&rest[4..size+4]){return None}
  seen|=bit;
  offset=offset.checked_add(size+4)?;
 }
}
fn extension_data_valid(kind:u16,bytes:&[u8])->bool{
 match kind{
  14=>bytes.len()>=64 && bytes[32..64].iter().all(|&b|b==0),
  6=>!bytes.is_empty() && bytes[0]==1,
  1=>bytes.len()>=108,
  _=>true,
 }
}

#[inline(never)]
pub fn required_quote_account_len(data:&[u8])->Option<usize>{
 let mut size=170usize;
 if data.len()==82{return Some(size)}
 if data.len()<167 || data[82..165].iter().any(|byte|*byte!=0) || data[165]!=1{return None}
 let tlv=&data[166..];
 let mut cursor=0usize;let mut seen=0u64;
 loop{
  let rest=tlv.get(cursor..)?;
  if rest.len()<2{return Some(size)}
  let kind=u16::from_le_bytes(rest[..2].try_into().unwrap());
  if kind==0{return Some(size)}
  if rest.len()<4{return None}
  let end=u16::from_le_bytes(rest[2..4].try_into().unwrap()) as usize+4;
  if end>rest.len(){return None}
  if let Some(payload)=match kind {1=>Some(8usize),9=>Some(0),14=>Some(1),26=>Some(0),_=>None}{
   let mask=1u64<<kind;
   if seen&mask==0{size=size.checked_add(4)?.checked_add(payload)?;seen|=mask;}}
  cursor=cursor.checked_add(end)?;
 }
}

/// Native fee schedule shape observed at the original pre-fee helper boundary.
#[repr(C)]
#[derive(Clone, Copy)]
pub struct Fee {
    pub epoch: u64,
    pub maximum_fee: u64,
    pub basis_points: u16,
}

impl Fee {
    #[inline(never)]
    pub fn calculate_fee(&self, pre_fee_amount: u64) -> Option<u64> {
        if pre_fee_amount == 0 {
            return Some(0);
        }
        let basis_points = self.basis_points as u128;
        if basis_points == 0 {
            return Some(0);
        }
        let numerator = (pre_fee_amount as u128).checked_mul(basis_points)?;
        let raw_fee: u64 = numerator.checked_add(10_000)?
            .checked_sub(1)?.checked_div(10_000)?.try_into().ok()?;
        Some(core::cmp::min(raw_fee, self.maximum_fee))
    }

    #[inline(never)]
    pub fn calculate_pre_fee_amount(&self, post_fee_amount: u64) -> Option<u64> {
        let basis_points = self.basis_points as u128;
        match (basis_points, post_fee_amount) {
            (0, _) => Some(post_fee_amount),
            (_, 0) => Some(0),
            (10_000, _) => self.maximum_fee.checked_add(post_fee_amount),
            _ => {
                let numerator = (post_fee_amount as u128).checked_mul(10_000)?;
                let denominator = 10_000u128.checked_sub(basis_points)?;
                let pre_fee_amount = numerator.checked_add(denominator)?
                    .checked_sub(1)?.checked_div(denominator)?;
                if pre_fee_amount.checked_sub(post_fee_amount as u128)? >= self.maximum_fee as u128 {
                    post_fee_amount.checked_add(self.maximum_fee)
                } else {
                    u64::try_from(pre_fee_amount).ok()
                }
            }
        }
    }
}

#[repr(C)]
#[derive(Clone, Copy)]
pub struct TransferFeeConfig {
    pub older_transfer_fee: Fee,
    pub newer_transfer_fee: Fee,
}

impl TransferFeeConfig {
    #[inline]
    pub fn get_epoch_fee(&self, epoch: u64) -> &Fee {
        if epoch >= self.newer_transfer_fee.epoch {
            &self.newer_transfer_fee
        } else {
            &self.older_transfer_fee
        }
    }
}

const MINT_LEN: usize = 82;
const ACCOUNT_LEN: usize = 165;

#[inline(always)]
fn read_u64(data: &[u8], offset: usize) -> u64 {
    unsafe { core::ptr::read_unaligned(data.as_ptr().add(offset) as *const u64) }
}

#[inline(always)]
fn read_u16(data: &[u8], offset: usize) -> u16 {
    unsafe { core::ptr::read_unaligned(data.as_ptr().add(offset) as *const u16) }
}

/// Native Token-2022 mint parser: returns the TransferFeeConfig extension, if any.
#[inline(never)]
pub fn get_transfer_fee_config(data: &[u8]) -> Result<Option<TransferFeeConfig>, ()> {
    if data.len() == MINT_LEN {
        return Ok(None);
    }
    if data.len() < ACCOUNT_LEN + 2 {
        return Err(());
    }
    if data[MINT_LEN..ACCOUNT_LEN].iter().any(|b| *b != 0) {
        return Err(());
    }
    if data[ACCOUNT_LEN] != 1 {
        return Err(());
    }
    let tlv = &data[ACCOUNT_LEN + 1..];
    let mut offset = 0usize;
    let mut config = None;
    loop {
        let rest = tlv.get(offset..).ok_or(())?;
        if !(rest.len() >= 2) {
            return Ok(config);
        }
        let tag = read_u16(rest, 0);
        match tag {
            0 => break, _ => {}
        }
        if !(rest.len() >= 4) {
            return Err(());
        }
        let length = read_u16(rest, 2) as usize;
        let entry_len = length + 4;
        if !(entry_len <= rest.len()) {
            return Err(());
        }
        if tag < 2 {
            if config.is_some() {
                return Err(());
            }
            if length < 108 {
                return Err(());
            }
            config = Some(TransferFeeConfig {
                older_transfer_fee: Fee {
                    epoch: read_u64(rest, 76),
                    maximum_fee: read_u64(rest, 84),
                    basis_points: read_u16(rest, 92),
                },
                newer_transfer_fee: Fee {
                    epoch: read_u64(rest, 94),
                    maximum_fee: read_u64(rest, 102),
                    basis_points: read_u16(rest, 110),
                },
            });
        }
        offset = offset.checked_add(entry_len).ok_or(())?;
    }
    Ok(config)
}

