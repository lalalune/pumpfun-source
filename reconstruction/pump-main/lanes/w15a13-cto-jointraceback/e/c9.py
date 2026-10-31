EDITS=[('swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);', 'swept=match skip{true=>0,false=>sweep(&ctx,&holder_key)?};')]
HYP='sweep gate match skip true first'
