EDITS=[('swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);', 'swept=if skip{0}else{match sweep(&ctx,&holder_key){Err(e)=>return Err(e),Ok(v)=>v}};')]
HYP='sweep gate with an if-let Err early return (RPO puts the continuation before the Err block): swept=if skip{0}else{match sweep(&ctx,&holder_key){Err(e)=>return Err(e),Ok(v)=>v}};'
