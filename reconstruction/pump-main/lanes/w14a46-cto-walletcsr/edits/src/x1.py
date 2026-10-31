EDITS=[["swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);", "swept=if collect_old{0}else{(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0)};"]]
