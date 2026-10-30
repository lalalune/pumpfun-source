A='''    let buyback=crate::protocol_fee_split(buyback_bps,protocol_fee,is_mayhem!=0).0; let post_buyback=match post{Some(p)=>crate::protocol_fee_split(buyback_bps,p.fees.protocol_fee,is_mayhem!=0).0,None=>0};'''
def rep(s,new):
    assert A in s; return s.replace(A,new)
