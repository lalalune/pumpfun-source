exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a45-cto-lv3frame/trials/s_map.py').read())
def _f(s):
    a='let sk=a.sharing_config.key();let mut target=holder_key;validate('
    assert s.count(a)==1
    return s.replace(a,'let mut target=holder_key;let sk=a.sharing_config.key();validate(')
EDITS=EDITS+[_f]
