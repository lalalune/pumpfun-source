exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a45-cto-lv3frame/trials/s_map.py').read())
def _f(s):
    a=' if holder&&!st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}\n\n *out=if hb{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{'; assert s.count(a)==1
    return s.replace(a,' *out=if hb{if !st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}\n\n  if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{')
EDITS=EDITS+[_f]
