V338="unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};}None"
MUT=[("let st=CtoState{","let mut st=CtoState{"),("validate(&st,","validate(&mut st,"),("fn validate(st:&CtoState,","fn validate(st:&mut CtoState,")]
V={
 'b0':(False,""),
 'v_mf1':(True,"st.max_fee=1;"),
 'v_mff':(True,"st.max_fee=f;"),
 'v_mayT':(True,"st.mayhem=true;"),
 'v_mayF':(True,"st.mayhem=false;"),
 'v_fcF':(True,"st.fee_configurable=false;"),
 'v_qlT':(True,"st.quote_locked=true;"),
 'v_mut0':(True,""),
}
import sys
for k,(m,s) in V.items():
    e=(MUT if m else [])+[(V338,s+"}None")]
    open(k+'.py','w').write('EDITS='+repr(e)+'\n')
