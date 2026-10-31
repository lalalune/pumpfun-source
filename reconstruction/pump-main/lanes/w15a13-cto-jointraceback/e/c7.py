EDITS=[('swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);', 'swept=if let false=skip{sweep(&ctx,&holder_key)?}else{0};')]
HYP='sweep gate if let false=skip'
