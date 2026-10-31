exec(open("/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a67-cto-h7src/e/common.py").read())
V="let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;"
F="fn validate(st:&CtoState"
EDITS=[(F,'#[inline]'+F)]
