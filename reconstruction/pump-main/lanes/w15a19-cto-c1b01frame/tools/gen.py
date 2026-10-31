import json,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w15a19-cto-c1b01frame')
_CB="let cashback=!holder&&st.cashback;"
_NA="else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}"
_NS="else{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};"
_CO="!st.holder_reward&&st.creator!=Pubkey::default()"
c1=[(_CB,"let mut cashback=false;"),
    (_NA,"else{sharing_update=Some(args.0);cashback=st.cashback;target=a.bonding_curve.creator;(false,true)}}"),
    (_NS,"else{cashback=!holder&&st.cashback;("+_CO+",true)};")]
SIG='holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>'
CALL='validate(&st,hopt,fee,new,&holder_key,&sk)'
RV='read_volatile(holder_key as *const Pubkey as *const u8)'
b01=[(SIG,'holder_key:Pubkey,sharing:&Pubkey)->Result<Pubkey>'),(CALL,'validate(&st,hopt,fee,new,holder_key,&sk)'),
     ('*holder_key}else{','holder_key}else{'),('t==*holder_key{','t==holder_key{'),
     ('unsafe{core::ptr::'+RV+'};if !st','unsafe{core::ptr::read_volatile(&holder_key as *const Pubkey as *const u8)};if !st'),
     (RV+'};}None','read_volatile(&holder_key as *const Pubkey as *const u8)};}None')]
b02=[(a,b) for a,b in b01 if a!='t==*holder_key{']+[('if t==*sharing||t==*holder_key{','if t==holder_key||t==*sharing{')]
V={'m0':[],'c1':c1,'b01':b01,'b02':b02,'c1b01':c1+b01,'c1b02':c1+b02}
import sys
extra=json.load(open(sys.argv[1])) if len(sys.argv)>1 else {}
V.update(extra)
for k,v in V.items(): open(f'{O}/e/{k}.py','w').write('EDITS='+json.dumps(v)+'\n')
print(' '.join(V))
