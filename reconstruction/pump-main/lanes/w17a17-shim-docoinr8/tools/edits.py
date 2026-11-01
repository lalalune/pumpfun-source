E={}
LIB={}
G='  if coin_present&do_coin{'
E['rw7']=[(G,'  if do_coin{')]
VA='unsafe{core::ptr::read_volatile(core::mem::transmute::<&&mut AdminCto,*const &AdminCto>(&ctx.accounts))}'
ATA='  if !collection_native||coin_present{anchor_spl::associated_token::create_idempotent('
# va1: ATA create re-derives the accounts pointer (volatile)
E['va1']=[(ATA,'  if !collection_native||coin_present{let a='+VA+'/*shim: re-derive the accounts pointer for the ATA create (orig r7 piece)*/;anchor_spl::associated_token::create_idempotent(')]
# va2: wallet body re-derives the accounts pointer once at collection_native
CN='  let collection_native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;'
E['va2']=[(CN,'  let a='+VA+'/*shim: re-derive the accounts pointer for the wallet body*/;let collection_native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;')]
VT='let mut target=validate(&st,hopt,fee,new,holder_key,&sk)?;'
RW='unsafe{let e=core::mem::ManuallyDrop::new(e);let w=&*e as *const anchor_lang::error::Error as *const usize;core::mem::transmute::<[usize;2],anchor_lang::error::Error>([*w,core::ptr::read_volatile(w.add(1))])}'
E['pe1']=[(VT,'let mut target=match validate(&st,hopt,fee,new,holder_key,&sk){Ok(t)=>t,Err(e)=>return Err('+RW+'/*shim: volatile reload of the validate error box word (Result payload phi r9)*/)};')]
E['pe2']=[(VT,'let mut target=validate(&st,hopt,fee,new,holder_key,&sk).map_err(|e|'+RW+'/*shim: volatile reload of the validate error box word (Result payload phi r9)*/)?;')]
E['pm0']=[(VT,'let mut target=match validate(&st,hopt,fee,new,holder_key,&sk){Ok(t)=>t,Err(e)=>return Err(e)};')]
E['pm1']=[(VT,'let mut target=match validate(&st,hopt,fee,new,holder_key,&sk){Ok(t)=>t,Err(e)=>{let e=core::mem::ManuallyDrop::new(e);return Err(unsafe{core::ptr::read_volatile(&*e)})/*shim: volatile reload of the validate error (Result payload phi r9)*/}};')]
VC='validate(&st,hopt,fee,new,holder_key,&sk)'
E['pv1']=[(VT,'let mut target={let mut r='+VC+';if let Err(e)=&mut r{unsafe{let p=(e as *mut anchor_lang::error::Error).cast::<usize>().add(1);core::ptr::write_volatile(p,core::ptr::read_volatile(p))}}r}/*shim: volatile round trip of the validate error box word (Result payload phi r9)*/?;')]
E['pv2']=[(VT,'let mut target={let r='+VC+';if let Err(e)=&r{unsafe{core::ptr::read_volatile((e as *const anchor_lang::error::Error).cast::<usize>().add(1))};}r}/*shim: volatile read of the validate error box word (Result payload phi r9)*/?;')]
E['cb1']=[('  curve.is_cashback_coin=cashback;','  curve.is_cashback_coin=unsafe{core::ptr::read_volatile(&cashback)}/*shim: cashback lives in a stack byte (ends the !holder head value before the wallet)*/;')]
E['cb3']=[('  curve.is_holder_reward=holder.unwrap_or(false);','  curve.is_holder_reward=unsafe{core::ptr::read_volatile(&holder)}/*shim: holder arg reloaded from the stack*/.unwrap_or(false);')]
