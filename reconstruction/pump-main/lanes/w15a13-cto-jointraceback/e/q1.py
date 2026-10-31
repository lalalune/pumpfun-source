EDITS=[('swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);', 'swept=if !skip{sweep(&ctx,&holder_key)?}else{0};')]
HYP='gate if !skip{sweep?}else{0} (sweep body is the then block)'
