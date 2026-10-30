def edit(s):
    a='    let first=add3(quote,protocol_fee,creator_fee)?;'
    assert a in s; return s.replace(a,'    let first=match add3(quote,protocol_fee,creator_fee){Ok(v)=>v,Err(e)=>return Err(e)};')
