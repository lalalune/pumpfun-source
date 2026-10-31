EDITS=[(' let swept;\n', ' let mut swept=0;\n'), ('swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);', 'if !skip{swept=sweep(&ctx,&holder_key)?;}')]
HYP='gate: let mut swept=0; if !skip{swept=sweep()?;}'
