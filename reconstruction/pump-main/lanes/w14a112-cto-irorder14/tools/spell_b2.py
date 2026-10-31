E284='if st.mayhem{return Err(error!(PumpError::CtoNotAllowedForMayhemCoin));}'
H283=('let holder=hopt==Some(true);\n',)
E289=' if st.holder_reward&&!(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}'
E296=' if holder&&!st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}'
R289='return Err(error!(PumpError::HolderRewardCreatorImmutable));'
R296='return Err(error!(PumpError::HolderRewardDisabled));'
def l283(x): return ('let holder=hopt==Some(true);\n','let holder=hopt==Some(true);'+x+'\n')
H289=(E289,' if st.holder_reward&&!holder{'+R289+'}')
V={
'F1':[l283('let disabled=holder&&!st.holder_reward&&!st.holder_enabled;'),(E296,' if disabled{'+R296+'}')],
'F2':[l283('let immut=st.holder_reward&&!holder;'),(E289,' if immut{'+R289+'}')],
'F3':[l283('let immut=st.holder_reward&&!holder;let disabled=holder&&!st.holder_reward&&!st.holder_enabled;'),(E289,' if immut{'+R289+'}'),(E296,' if disabled{'+R296+'}')],
'F4':[l283('let disabled=holder&!st.holder_reward&!st.holder_enabled;'),(E296,' if disabled{'+R296+'}')],
'F5':[(E289,' if st.holder_reward&&hopt!=Some(true){'+R289+'}')],
'F7':[(E289,' match st.holder_reward{true=>if !holder{'+R289+'},false=>{}}')],
'F8':[l283('let (mayhem,hr)=(st.mayhem,st.holder_reward);'),(E284,'if mayhem{return Err(error!(PumpError::CtoNotAllowedForMayhemCoin));}'),(E289,' if hr&&!holder{'+R289+'}'),(E296,' if holder&&!hr&&!st.holder_enabled{'+R296+'}')],
'F9':[(E284,'if st.mayhem{Err::<(),_>(error!(PumpError::CtoNotAllowedForMayhemCoin))?;}')],
'F10':[(E284,'if st.mayhem{Err::<(),_>(error!(PumpError::CtoNotAllowedForMayhemCoin))?;}'),H289],
'F11':[(E289,' if st.holder_reward{if !holder{'+R289+'}}')],
'F12':[(E289,' if st.holder_reward&&!holder{Err::<(),_>(error!(PumpError::HolderRewardCreatorImmutable))?;}')],
'F2h':[l283('let immut=st.holder_reward&&!(hopt==Some(true));'),(E289,' if immut{'+R289+'}')],
}
for k,v in V.items(): open(k+'.py','w').write('EDITS='+repr(v)+'\n')
