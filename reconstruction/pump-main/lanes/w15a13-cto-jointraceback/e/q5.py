EDITS=[('swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);', 'swept=match !skip{true=>sweep(&ctx,&holder_key)?,false=>0};')]
HYP='gate match !skip{true=>sweep?,false=>0}'
