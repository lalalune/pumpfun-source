EDITS=[('swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);','swept=if skip{Ok(0)}else{sweep(&ctx,&holder_key)}?;')]
