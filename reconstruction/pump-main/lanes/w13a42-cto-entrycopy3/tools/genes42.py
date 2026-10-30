# w13a42 entry-region spellings (main 53abf28). Each (old,new) must occur once; newline count kept.
X={}
EC='let hopt=holder;let holder=hopt==Some(true);let cashback=st.cashback&&!holder;'
X['cb_band']=[(EC,'let hopt=holder;let holder=hopt==Some(true);let cashback=st.cashback&!holder;')]
X['cb_nband']=[(EC,'let hopt=holder;let holder=hopt==Some(true);let cashback=!holder&st.cashback;')]
X['h_unwrap']=[(EC,'let hopt=holder;let holder=hopt.unwrap_or(false);let cashback=st.cashback&&!holder;')]
X['h_unwrap_rev']=[(EC,'let hopt=holder;let holder=hopt.unwrap_or(false);let cashback=!holder&&st.cashback;')]
X['h_matches']=[(EC,'let hopt=holder;let holder=matches!(hopt,Some(true));let cashback=st.cashback&&!holder;')]
X['h_matches_rev']=[(EC,'let hopt=holder;let holder=matches!(hopt,Some(true));let cashback=!holder&&st.cashback;')]
X['h_isa']=[(EC,'let hopt=holder;let holder=hopt.is_some_and(|h|h);let cashback=st.cashback&&!holder;')]
X['cb_ifrev']=[(EC,'let hopt=holder;let holder=hopt==Some(true);let cashback=if !holder{st.cashback}else{false};')]
VC='let cashback=if holder{false}else{st.cashback};'
X['v_cb_and']=[(VC,'let cashback=!holder&&st.cashback;')]
X['v_cb_and2']=[(VC,'let cashback=st.cashback&&!holder;')]
VH='Result<Pubkey>{let holder=hopt==Some(true);'
X['v_h_unwrap']=[(VH,'Result<Pubkey>{let holder=hopt.unwrap_or(false);')]
X['v_h_matches']=[(VH,'Result<Pubkey>{let holder=matches!(hopt,Some(true));')]
VR='if st.holder_reward&&!(hopt==Some(true))'
X['v_hr_holder']=[(VR,'if st.holder_reward&&!holder')]
X['v_hr_ne']=[(VR,'if st.holder_reward&&hopt!=Some(true)')]
