EDITS=[('swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);', 'swept=if skip{0}else{let r=sweep(&ctx,&holder_key);if r.is_err(){return r.map(|_|());}r.unwrap_or(0)};')]
HYP='sweep gate with an if-let Err early return (RPO puts the continuation before the Err block): swept=if skip{0}else{let r=sweep(&ctx,&holder_key);if r.is_err(){return r.map(|_|());}r.unwrap_or(0)};'
