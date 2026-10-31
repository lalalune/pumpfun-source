# variant edits for lines 298-338 (each keeps newline count and every line!())
L306='let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};'
E306='return Err(error!(PumpError::CtoNewCreatorRequired))'
L298='if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{'
L307='if t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((t,Pubkey::default())));}'
L312='if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};'
E312='return Err(error!(PumpError::InvalidCreator))'
L314='let cashback=if holder{false}else{st.cashback};'
L326='match fee{Some(f)=>{if st.quote_locked{'
L330='if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}'
L338a='if f==0||f>st.max_fee{'
END=';}None=>{}}\n Ok(target)}'
V={
 'le306':[(L306,'let Some(t)=new else{'+E306+';};')],
 'mS306':[(L306,'let t=match new{Some(t)=>t,None=>'+E306+'};')],
 'mN306':[(L306,'let t=match new{None=>'+E306+',Some(t)=>t};')],
 'mW306':[(L306,'let t=match new{Some(t)=>t,_=>'+E306+'};')],
 'isn306':[(L306,'if new.is_none(){'+E306+';}let t=new.unwrap();')],
 'isne306':[(L306,'let t=if new.is_none(){'+E306+';}else{new.unwrap()};')],
 'ifN306':[(L306,'let t=if let None=new{'+E306+';}else{new.unwrap()};')],
 'ref306':[(L306,'let t=if let Some(t)=&new{*t}else{'+E306+';};')],
 'oke306':[(L306,'let t=new.ok_or_else(||error!(PumpError::CtoNewCreatorRequired))?;')],
 'iss306':[(L306,'let t=if new.is_some(){new.unwrap()}else{'+E306+';};')],
 'ifl298':[(L298,'if holder{if let Some(_)=new{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{')],
 'nn298':[(L298,'if holder{if !new.is_none(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{')],
 'ne298':[(L298,'if holder{if new!=None{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{')],
 'm298':[(L298,'if holder{match new{Some(_)=>return Err(error!(PumpError::CtoNewCreatorNotAllowed)),None=>{}}*holder_key}else{')],
 'sw307':[(L307,'if Pubkey::default()==t{return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((t,Pubkey::default())));}')],
 'sw312':[(L312,'if t==*holder_key||t==*sharing{'+E312+';}t};')],
 'rv312':[(L312,'if *sharing==t||*holder_key==t{'+E312+';}t};')],
 'sp312':[(L312,'if t==*sharing{'+E312+';}if t==*holder_key{'+E312+';}t};')],
 'nd312':[(L312,'if t!=*sharing&&t!=*holder_key{t}else{'+E312+';}};')],
 'ct312':[(L312,'if [*sharing,*holder_key].contains(&t){'+E312+';}t};')],
 'cb314a':[(L314,'let cashback=!holder&&st.cashback;')],
 'cb314b':[(L314,'let cashback=st.cashback&&!holder;')],
 'cb314c':[(L314,'let cashback=if !holder{st.cashback}else{false};')],
 'cb330':[(L330,'if cashback==true{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}')],
 'fNf':[(L326,'match fee{None=>{},Some(f)=>{if st.quote_locked{'),(END,';}}\n Ok(target)}')],
 'fil':[(L326,'if let Some(f)=fee{if st.quote_locked{'),(END,';}\n Ok(target)}')],
 'fle':[(L326,'let Some(f)=fee else{return Ok(target)};if st.quote_locked{'),(END,';\n Ok(target)}')],
 'f338a':[(L338a,'if f>st.max_fee||f==0{')],
 'f338b':[(L338a,'if !(1..=st.max_fee).contains(&f){')],
 'f338c':[(L338a,'if f<1||f>st.max_fee{')],
}
CS='fee_configurable:bool}'
CI='fee_configurable:a.global.creator_fee_configurable};'
V2={
 'hs1':[(CS,'fee_configurable:bool,has_new:bool}'),(CI,'fee_configurable:a.global.creator_fee_configurable,has_new:new.is_some()};'),(L306,'let t=if st.has_new{new.unwrap_or_default()}else{'+E306+';};')],
 'hs1n':[(CS,'fee_configurable:bool,has_new:bool}'),(CI,'fee_configurable:a.global.creator_fee_configurable,has_new:new.is_some()};'),(L306,'if !st.has_new{'+E306+';}let t=new.unwrap_or_default();')],
 'hs1m':[(CS,'fee_configurable:bool,has_new:bool}'),(CI,'fee_configurable:a.global.creator_fee_configurable,has_new:new.is_some()};'),(L306,'let t=match (st.has_new,new){(true,Some(t))=>t,_=>'+E306+'};')],
 'hp1':[('fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,','fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,has:bool,'),('validate(&st,hopt,fee,new,&holder_key,&sk)','validate(&st,hopt,fee,new,new.is_some(),&holder_key,&sk)'),(L306,'let t=if has{new.unwrap_or_default()}else{'+E306+';};')],
 'tp306':[(L306,'let t=match (new.is_some(),new){(true,Some(t))=>t,_=>'+E306+'};')],
}
V.update(V2)
