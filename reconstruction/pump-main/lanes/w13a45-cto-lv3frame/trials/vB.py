exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a45-cto-lv3frame/trials/s_map.py').read())
def _f(s):
    for a,b in [('if shared{st.creator}else{t}};','t};'),('else{(Some(args.0),false,true)}','else{target=st.creator;(Some(args.0),false,true)}')]:
        assert s.count(a)==1,a; s=s.replace(a,b)
    return s
EDITS=EDITS+[_f]
