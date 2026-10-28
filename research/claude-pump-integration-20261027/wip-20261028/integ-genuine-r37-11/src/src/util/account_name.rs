use anchor_lang::error::{Error,ErrorOrigin};

#[inline(never)]
pub fn with_owned_name(mut error:Error,name:&String)->Error{
    match &mut error{
        Error::AnchorError(value)=>value.error_origin=Some(ErrorOrigin::AccountName(name.clone())),
        Error::ProgramError(value)=>value.error_origin=Some(ErrorOrigin::AccountName(name.clone())),
    }
    error
}
