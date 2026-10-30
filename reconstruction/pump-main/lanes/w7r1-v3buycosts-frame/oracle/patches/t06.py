import runpy; c=runpy.run_path(__file__.rsplit('/',1)[0]+'/common.py')
def edit(s): return c['rep'](s,'    let buyback=crate::protocol_fee_split(buyback_bps,protocol_fee,is_mayhem!=0).0; let post_buyback; if let Some(p)=post{post_buyback=crate::protocol_fee_split(buyback_bps,p.fees.protocol_fee,is_mayhem!=0).0}else{post_buyback=0}')
