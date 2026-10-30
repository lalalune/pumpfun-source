exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a45-cto-lv3frame/trials/s_map.py').read())
def _f(s):
    a=' *out=if hb{'; assert s.count(a)==1
    return s.replace(a,' *out=if holder{')
EDITS=EDITS+[_f]
