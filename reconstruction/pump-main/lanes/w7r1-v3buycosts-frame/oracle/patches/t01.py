import runpy; c=runpy.run_path(__file__.rsplit('/',1)[0]+'/common.py')
def edit(s): return c['rep'](s,'    let buyback={let s=crate::protocol_fee_split(buyback_bps,protocol_fee,is_mayhem!=0);s.0}; let post_buyback=match post{Some(p)=>{let s=crate::protocol_fee_split(buyback_bps,p.fees.protocol_fee,is_mayhem!=0);s.0},None=>0};')
