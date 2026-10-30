import runpy; c=runpy.run_path(__file__.rsplit('/',1)[0]+'/common.py')
def edit(s):
    s=c['rep'](s,'    let s1=crate::protocol_fee_split(buyback_bps,protocol_fee,is_mayhem!=0); let s2=match post{Some(p)=>crate::protocol_fee_split(buyback_bps,p.fees.protocol_fee,is_mayhem!=0),None=>(0,0)};')
    a='let total_buyback=buyback.checked_add(post_buyback)'
    assert a in s; return s.replace(a,'let total_buyback=s1.0.checked_add(s2.0)')
