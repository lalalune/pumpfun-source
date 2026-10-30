import runpy; c=runpy.run_path(__file__.rsplit('/',1)[0]+'/common.py')
def edit(s): return c['rep'](s,'    let buyback=crate::protocol_fee_split(buyback_bps,protocol_fee,is_mayhem!=0).0; let post_fee=post.map(|p|p.fees.protocol_fee); let post_buyback=match post_fee{Some(f)=>crate::protocol_fee_split(buyback_bps,f,is_mayhem!=0).0,None=>0};')
