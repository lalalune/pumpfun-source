EDITS=[('swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);','swept=if let Some(r)=(!skip).then(||sweep(&ctx,&holder_key)){r?}else{0};')]
