exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a45-cto-lv3frame/trials/s_map.py').read())
def _f(s):
    for a,b in [('out:&mut Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);', 'out:&mut Pubkey)->Result<Pubkey>{let nh=hopt!=Some(true);'), (' if holder&&!st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}', ' if !nh&&!st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}'), (' let cashback=if holder{false}else{st.cashback};', ' let cashback=if nh{st.cashback}else{false};')]:
        assert s.count(a)==1,a; s=s.replace(a,b)
    return s
EDITS=EDITS+[_f]
