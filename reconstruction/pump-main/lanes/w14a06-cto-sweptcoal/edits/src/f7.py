EDITS=[('swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);','swept=(!skip).then(||sweep(&ctx,&holder_key)).unwrap_or(Ok(0)).and_then(|v|Ok(v))?;')]
