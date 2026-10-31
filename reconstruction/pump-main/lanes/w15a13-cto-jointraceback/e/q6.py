EDITS=[('swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);', 'if skip{swept=0;}else{swept=sweep(&ctx,&holder_key)?;}')]
HYP='gate: deferred swept assigned in both arms, skip arm first'
