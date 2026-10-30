SIG="holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{"
T298="return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}"
T312="if t==*sharing||t==*holder_key{"
CALL="validate(&st,hopt,fee,new,&holder_key,&sk)?"
def mk(hk_val,sh_val,order):
    sig="holder_key:%sPubkey,sharing:%sPubkey)->Result<Pubkey>{"%('' if hk_val else '&','' if sh_val else '&')
    h='holder_key' if hk_val else '*holder_key'; s='sharing' if sh_val else '*sharing'
    t312='if t==%s||t==%s{'%((h,s) if order=='hs' else (s,h))
    call="validate(&st,hopt,fee,new,%sholder_key,%ssk)?"%('' if hk_val else '&','' if sh_val else '&')
    return [(SIG,sig),(T298,T298.replace('*holder_key}',h+'}')),(T312,t312),(CALL,call)]
