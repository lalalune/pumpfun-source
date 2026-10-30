exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a45-cto-lv3frame/trials/s_map.py').read())
def _f(s):
    for a,b in [(' if st.holder_reward&&!(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}',' if st.holder_reward{if !(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}}'),(' if holder&&!st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}',' else if holder&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}')]:
        assert s.count(a)==1,a; s=s.replace(a,b)
    return s
EDITS=EDITS+[_f]
