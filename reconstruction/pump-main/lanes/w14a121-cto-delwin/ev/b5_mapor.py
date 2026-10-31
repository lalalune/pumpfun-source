EDITS=[("swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);","swept=(!skip).then(||sweep(&ctx,&holder_key)).map_or(Ok(0),|r|r)?;")]
