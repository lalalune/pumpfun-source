EDITS=[('swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);','swept=match (!skip).then(||sweep(&ctx,&holder_key)){Some(Err(e))=>return Err(e),Some(Ok(v))=>v,None=>0};')]
