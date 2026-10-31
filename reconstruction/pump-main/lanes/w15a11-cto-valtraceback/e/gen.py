import json,os
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a11-cto-valtraceback'
E312='if t==*sharing||t==*holder_key{'
V={
'v01':[(E312,'if t==*holder_key||t==*sharing{')],
'v02':[('if st.holder_reward&&!(hopt==Some(true)){','if st.holder_reward&&!holder{')],
'v03':[('if holder&&!st.holder_reward&&!st.holder_enabled{','if holder&&!(st.holder_reward||st.holder_enabled){')],
'v04':[('if new.is_some(){','if let Some(_)=new{')],
'v05':[('if new.is_some(){','if new!=None{')],
'v06':[('let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};','let t=match new{Some(t)=>t,None=>return Err(error!(PumpError::CtoNewCreatorRequired))};')],
'v08':[('let cashback=if holder{false}else{st.cashback};','let cashback=!holder&&st.cashback;')],
'v09':[('match fee{Some(f)=>{if st.quote_locked{','if let Some(f)=fee{if st.quote_locked{'),('read_volatile(holder_key as *const Pubkey as *const u8)};}None=>{}}','read_volatile(holder_key as *const Pubkey as *const u8)};}')],
'v10':[('if f==0||f>st.max_fee{','if !(1..=st.max_fee).contains(&f){')],
'v12':[('if f==0||f>st.max_fee{','if f>st.max_fee||f==0{')],
'v14':[('->Result<Pubkey>{let holder=hopt==Some(true);','->Result<Pubkey>{let holder=matches!(hopt,Some(true));')],
'v21':[('if holder&&!st.holder_reward&&!st.holder_enabled{','if !st.holder_reward&&!st.holder_enabled&&holder{')],
'v22':[('if st.holder_reward&&!(hopt==Some(true)){','if !(hopt==Some(true))&&st.holder_reward{')],
'v24':[('let cashback=if holder{false}else{st.cashback};','let cashback=st.cashback&&!holder;')],
'v25':[('let cashback=if holder{false}else{st.cashback};',''),('if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}','if !holder&&st.cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}')],
'v26':[('if holder&&!st.holder_reward&&!st.holder_enabled{','if holder&&!st.holder_reward&&!st.holder_enabled==true{')],
'v27':[('let target=if holder{if new.is_some(){','let target=if hopt==Some(true){if new.is_some(){')],
'v28':[('if st.mayhem{return','if st.mayhem==true{return')],
'v29':[('if t==Pubkey::default(){','if t==Pubkey::new_from_array([0;32]){')],
'v30':[('if f==0||f>st.max_fee{','if f==0{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}if f>st.max_fee{')],
'v31':[('if st.quote_locked{return Err(error!(PumpError::CreatorFeeNotConfigurableForQuote));}','if st.quote_locked{Err(error!(PumpError::CreatorFeeNotConfigurableForQuote))?;}')],
'v32':[('if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};','if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}else{t}};')],
'v33':[('{let holder=hopt==Some(true);','{let holder=hopt==Some(true);let new=new;')],
}
os.makedirs(O+'/e',exist_ok=True)
for k,v in V.items(): open(f'{O}/e/{k}.py','w').write('EDITS='+json.dumps(v)+'\n')
print(' '.join(V))
SIG='holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>'
CALL='validate(&st,hopt,fee,new,&holder_key,&sk)'
RV='read_volatile(holder_key as *const Pubkey as *const u8)'
def hkval():
    return [(SIG,'holder_key:Pubkey,sharing:&Pubkey)->Result<Pubkey>'),(CALL,'validate(&st,hopt,fee,new,holder_key,&sk)'),
            ('*holder_key}else{','holder_key}else{'),('t==*holder_key{','t==holder_key{'),
            ('unsafe{core::ptr::'+RV+'};if !st','unsafe{core::ptr::read_volatile(&holder_key as *const Pubkey as *const u8)};if !st'),
            (RV+'};}None','read_volatile(&holder_key as *const Pubkey as *const u8)};}None')]
def shval():
    return [(SIG,'holder_key:&Pubkey,sharing:Pubkey)->Result<Pubkey>'),(CALL,'validate(&st,hopt,fee,new,&holder_key,sk)'),('t==*sharing','t==sharing')]
W={
'b01':hkval()+[],
'b03':shval(),
}
# b02: hkval + 312 swap (holder first)
W['b02']=[(a,b) for a,b in hkval() if a!='t==*holder_key{']+[('if t==*sharing||t==*holder_key{','if t==holder_key||t==*sharing{')]
W['b04']=[(a,b) for a,b in shval() if a!='t==*sharing']+[('if t==*sharing||t==*holder_key{','if t==*holder_key||t==sharing{')]
# both by value + holder first
both=[(SIG,'holder_key:Pubkey,sharing:Pubkey)->Result<Pubkey>'),(CALL,'validate(&st,hopt,fee,new,holder_key,sk)'),('*holder_key}else{','holder_key}else{'),
      ('if t==*sharing||t==*holder_key{','if t==holder_key||t==sharing{'),
      ('unsafe{core::ptr::'+RV+'};if !st','unsafe{core::ptr::read_volatile(&holder_key as *const Pubkey as *const u8)};if !st'),
      (RV+'};}None','read_volatile(&holder_key as *const Pubkey as *const u8)};}None')]
W['b05']=both
W['b06']=[(a,b.replace('if t==holder_key||t==sharing{','if t==sharing||t==holder_key{')) for a,b in both]
for k,v in W.items(): open(f'{O}/e/{k}.py','w').write('EDITS='+json.dumps(v)+'\n')
print(' '.join(W))
