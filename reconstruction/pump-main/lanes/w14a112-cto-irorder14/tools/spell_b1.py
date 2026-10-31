E284='if st.mayhem{return Err(error!(PumpError::CtoNotAllowedForMayhemCoin));}'
R='return Err(error!(PumpError::CtoNotAllowedForMayhemCoin))'
H289=(' if st.holder_reward&&!(hopt==Some(true)){',' if st.holder_reward&&!holder{')
E289=' if st.holder_reward&&!(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}'
E296=' if holder&&!st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}'
R289='return Err(error!(PumpError::HolderRewardCreatorImmutable));'
R296='return Err(error!(PumpError::HolderRewardDisabled));'
V={
'A1':[(E284,'if !st.mayhem{}else{'+R+';}')],
'A2':[(E284,'match st.mayhem{false=>{},true=>'+R+'}')],
'A3':[(E284,'match st.mayhem{true=>'+R+',false=>{}}')],
'A4':[(E289,' else if st.holder_reward&&!holder{'+R289+'}'),(E296,' else if holder&&!st.holder_reward&&!st.holder_enabled{'+R296+'}')],
'A5':[(E289,' if st.holder_reward{if !holder{'+R289+'}}'),(E296,' else if holder&&!st.holder_enabled{'+R296+'}')],
'A6':[(E284,'match (st.mayhem,st.holder_reward){(true,_)=>'+R+','),(E289,' (false,true)=>if !holder{'+R289+'},'),(E296,' (false,false)=>if holder&&!st.holder_enabled{'+R296+'}}')],
'A7':[(E284,'if st.mayhem==true{'+R+';}')],
'A8':[('let holder=hopt==Some(true);\n','let holder=hopt==Some(true);let hr=st.holder_reward;\n'),(E289,' if hr&&!holder{'+R289+'}'),(E296,' if holder&&!hr&&!st.holder_enabled{'+R296+'}')],
'A9':[(E289,' if st.holder_reward{if !holder{'+R289+'}}else{'),(E296,' if holder&&!st.holder_enabled{'+R296+'}}')],
'H0':[H289],
}
for k,v in V.items():
    open(k+'.py','w').write('EDITS='+repr(v)+'\n')
    if k not in('H0','A4','A5','A6','A8','A9'): open(k+'h.py','w').write('EDITS='+repr(v+[H289])+'\n')
