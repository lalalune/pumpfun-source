# Spellings added by w14a134 (append to w14a104 sp/defs.py; uses its L296/L298/_VH/_T306 names)
# w14a134 headroute306 candidates
V['tagb']=[(_VH,'->Result<Pubkey>{let holder=hopt==Some(true);let has_new=new.is_some();'),(' let target=if holder{if new.is_some(){',' let target=if holder{if has_new{')]
V['s296G']=[(L296,' if holder&&!st.holder_reward&&!st.holder_enabled{Err(error!(PumpError::HolderRewardDisabled))}else{Ok(())}?;')]
V['s306G']=[(_T306,'let t=if let Some(t)=new{Ok(t)}else{Err(error!(PumpError::CtoNewCreatorRequired))}?;')]
V['s298G']=[(' let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}',' let target=if holder{if new.is_some(){Err(error!(PumpError::CtoNewCreatorNotAllowed))}else{Ok(())}?;')]
V['mN306']=[(_T306,'let t=match new{None=>return Err(error!(PumpError::CtoNewCreatorRequired)),Some(t)=>t};')]
