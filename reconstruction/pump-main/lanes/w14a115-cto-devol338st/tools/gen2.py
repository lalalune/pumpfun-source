V338="unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};}None"
CALL=[("let st=CtoState{","let mut st=CtoState{"),("validate(&st,","validate(&mut st,")]
SIG="fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{"
def sig(new_head,pre=""): return [(SIG,new_head+pre)]
V={
 'w_rb_mf1':CALL+sig("fn validate(stm:&mut CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{","let st=&*stm;")+[(V338,"stm.max_fee=1;}None")],
 'w_rb_mff':CALL+sig("fn validate(stm:&mut CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{","let st=&*stm;")+[(V338,"stm.max_fee=f;}None")],
 'w_rb_0':CALL+sig("fn validate(stm:&mut CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{","let st=&*stm;")+[(V338,"}None")],
 'w_rb_fcF':CALL+sig("fn validate(stm:&mut CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{","let st=&*stm;")+[(V338,"stm.fee_configurable=false;}None")],
}
for k,e in V.items(): open(k+'.py','w').write('EDITS='+repr(e)+'\n')
