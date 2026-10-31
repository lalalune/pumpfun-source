EDITS=[('swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);','swept=match (!skip).then(||sweep(&ctx,&holder_key)){None=>0,Some(r)=>r?};')]
