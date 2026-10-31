EDITS=[('swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);', 'let r=if skip{Ok(0)}else{sweep(&ctx,&holder_key)};if let Err(e)=r{return Err(e);}swept=r.unwrap_or(0);')]
HYP='sweep gate with an if-let Err early return (RPO puts the continuation before the Err block): let r=if skip{Ok(0)}else{sweep(&ctx,&holder_key)};if let Err(e)=r{return Err(e);}swept=r.unwrap_or(0);'
