V338="unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};}None"
MUT=[("let st=CtoState{","let mut st=CtoState{"),("validate(&st,","validate(&mut st,"),("fn validate(st:&CtoState,","fn validate(st:&mut CtoState,")]
HR=[(" if st.holder_reward&&!(hopt==Some(true)){"," let hr=st.holder_reward;if hr&&!(hopt==Some(true)){"),("if holder&&!st.holder_reward&&!st.holder_enabled{","if holder&&!hr&&!st.holder_enabled{")]
V={'x_hr_0':MUT+HR+[(V338,"}None")],'x_hr_mf1':MUT+HR+[(V338,"st.max_fee=1;}None")],'x_hr_mayF':MUT+HR+[(V338,"st.mayhem=false;}None")],'x_hr_b0':HR+[(V338,"}None")]}
for k,e in V.items(): open(k+'.py','w').write('EDITS='+repr(e)+'\n')
