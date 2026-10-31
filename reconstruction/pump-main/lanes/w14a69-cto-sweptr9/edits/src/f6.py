EDITS=[('swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);','swept=match (!skip).then(||sweep(&ctx,&holder_key)).transpose(){Ok(v)=>v.unwrap_or(0),Err(e)=>return Err(e)};')]
