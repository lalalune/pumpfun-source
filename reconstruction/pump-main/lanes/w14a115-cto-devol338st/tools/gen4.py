V338="unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};}None"
V334="unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};if !st.fee_configurable"
MUT=[("let st=CtoState{","let mut st=CtoState{"),("validate(&st,","validate(&mut st,"),("fn validate(st:&CtoState,","fn validate(st:&mut CtoState,")]
HR=[(" if st.holder_reward&&!(hopt==Some(true)){"," let hr=st.holder_reward;if hr&&!(hopt==Some(true)){"),("if holder&&!st.holder_reward&&!st.holder_enabled{","if holder&&!hr&&!st.holder_enabled{")]
V={'x_hr_mff':MUT+HR+[(V338,"st.max_fee=f;}None")],'x_hr_fcF':MUT+HR+[(V338,"st.fee_configurable=false;}None")],
 'x_hr_both':MUT+HR+[(V338,"st.max_fee=1;}None"),(V334,"st.mayhem=false;if !st.fee_configurable")],
 'x_hr_334':MUT+HR+[(V334,"st.mayhem=false;if !st.fee_configurable")]}
for k,e in V.items(): open(k+'.py','w').write('EDITS='+repr(e)+'\n')
