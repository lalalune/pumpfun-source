EDITS=[('swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);', 'swept=(if skip{Ok(0)}else{sweep(&ctx,&holder_key)}).map(|v|v)?;')]
HYP='skip-polarity sweep gate keeping the ? after the join (IR order: sweep.exit then join): swept=(if skip{Ok(0)}else{sweep(&ctx,&holder_key)}).map(|v|v)?;'
