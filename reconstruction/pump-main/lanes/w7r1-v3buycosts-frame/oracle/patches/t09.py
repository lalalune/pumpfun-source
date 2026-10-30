def edit(s):
    a='let quote_transfer_fee=pool_quote.checked_sub(net).ok_or_else(gross_up_quote_error)?; Ok((pool_quote,total_buyback,quote_transfer_fee))'
    assert a in s; return s.replace(a,'let mut out=(pool_quote,total_buyback,0u64); out.2=pool_quote.checked_sub(net).ok_or_else(gross_up_quote_error)?; Ok(out)')
