exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a45-cto-lv3frame/trials/s_map.py').read())
def f(E):
    R=[]
    for a,b in E:
        b=b.replace('out:&mut Pubkey','out:&mut Result<Pubkey>')
        b=b.replace(' *out=if hb{',' *out=Ok(if hb{')
        b=b.replace('if shared{st.creator}else{t}};','if shared{st.creator}else{t}});')
        b=b.replace('let mut target=holder_key;validate(&st,hopt,holder,shared,fee,new,&holder_key,&sk,&mut target)?;','let mut tr:Result<Pubkey>=Ok(holder_key);validate(&st,hopt,holder,shared,fee,new,&holder_key,&sk,&mut tr)?;let mut target=tr?;')
        R.append((a,b))
    return R
EDITS=f(EDITS)
