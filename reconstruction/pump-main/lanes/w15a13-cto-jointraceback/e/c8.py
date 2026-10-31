EDITS=[('swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);', 'swept=match skip{false=>sweep(&ctx,&holder_key)?,true=>0};')]
HYP='sweep gate match skip false first'
