EDITS=[("swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);","swept=(!skip).then(||sweep(&ctx,&holder_key)).unwrap_or_else(||Ok(0))?;")]
