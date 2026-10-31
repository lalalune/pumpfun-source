EDITS=[('swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);', 'swept=(if skip{Ok(None)}else{sweep(&ctx,&holder_key).map(Some)})?.unwrap_or(0);')]
HYP='skip-polarity sweep gate keeping the ? after the join (IR order: sweep.exit then join): swept=(if skip{Ok(None)}else{sweep(&ctx,&holder_key).map(Some)})?.unwrap_or(0);'
