exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a45-cto-lv3frame/trials/s_map.py').read())
def _f(s):
    a=' if holder&&!st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}'; assert s.count(a)==1
    return s.replace(a,' if hopt.is_some_and(|h|h)&&!st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}')
EDITS=EDITS+[_f]
