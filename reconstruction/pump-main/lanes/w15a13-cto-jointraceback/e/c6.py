EDITS=[('swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);', 'swept=skip.then_some(Ok(0)).unwrap_or_else(||sweep(&ctx,&holder_key))?;')]
HYP='sweep gate skip.then_some(Ok(0)).unwrap_or_else(sweep)?'
