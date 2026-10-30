exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a45-cto-lv3frame/trials/s_map.py').read())
def _f(s):
    a='let sk=a.sharing_config.key();let mut target=holder_key;validate(&st,hopt,holder,shared,fee,new,&holder_key,&sk,&mut target)?;'
    assert s.count(a)==1
    return s.replace(a,'let mut target=holder_key;validate(&st,hopt,holder,shared,fee,new,&holder_key,&a.sharing_config.key(),&mut target)?;')
EDITS=EDITS+[_f]
