EDITS=[["swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);", "swept=(!(skip||collect_old)).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);"]]
