EDITS=[('swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);', 'if !skip{swept=sweep(&ctx,&holder_key)?;}else{swept=0;}')]
HYP='gate: deferred swept assigned in both arms, sweep arm first'
