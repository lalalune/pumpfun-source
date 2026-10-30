import runpy; c=runpy.run_path(__file__.rsplit('/',1)[0]+'/common.py')
def edit(s):
    s=c['rep'](s,'    let m=v3_flag(is_mayhem); let buyback=crate::protocol_fee_split(buyback_bps,protocol_fee,m).0; let post_buyback=match post{Some(p)=>crate::protocol_fee_split(buyback_bps,p.fees.protocol_fee,m).0,None=>0};')
    a='#[inline(never)]\npub fn gross_up_quote_error()'
    assert a in s; return s.replace(a,'#[inline(never)]\npub fn gross_up_quote_error()'.replace('#[inline(never)]\n','#[inline(never)]\n'),1).replace('fn add(a:u64,b:u64)','fn v3_flag(x:u8)->bool{x!=0} fn add(a:u64,b:u64)',1)
