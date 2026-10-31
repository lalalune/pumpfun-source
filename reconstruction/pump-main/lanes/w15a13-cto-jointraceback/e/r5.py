EDITS=[('swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);', 'swept=match skip{false=>Some(sweep(&ctx,&holder_key)),true=>None}.transpose()?.unwrap_or(0);')]
HYP='skip-polarity sweep gate keeping the ? after the join (IR order: sweep.exit then join): swept=match skip{false=>Some(sweep(&ctx,&holder_key)),true=>None}.transpose()?.unwrap_or(0);'
