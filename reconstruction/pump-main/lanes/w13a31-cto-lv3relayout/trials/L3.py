exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a31-cto-lv3relayout/e/lv3.py').read())
EDITS=EDITS+[('let mut target=holder_key;validate(&st,hopt,holder,shared,fee,new,&holder_key,&sk,&mut target)?;', 'let mut target=Pubkey::default();validate(&st,hopt,holder,shared,fee,new,&holder_key,&sk,&mut target)?;')]
