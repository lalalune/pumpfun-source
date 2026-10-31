EDITS=[('swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);','swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose().map(|o|o.unwrap_or(0))?;')]
