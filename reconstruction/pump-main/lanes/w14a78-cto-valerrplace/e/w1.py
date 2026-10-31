g={}; exec(open("/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a75-cto-and1polar/gen/k_st_ql_first.py").read(),g); EDITS=g['EDITS']
EDITS=EDITS+[('if holder&&!st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}', 'let bad=holder&&!st.holder_reward&&!st.holder_enabled;if bad{return Err(error!(PumpError::HolderRewardDisabled));}')]
