EDITS=[("swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);","swept=skip.then_some(0).map_or_else(||sweep(&ctx,&holder_key),Ok)?;")]
