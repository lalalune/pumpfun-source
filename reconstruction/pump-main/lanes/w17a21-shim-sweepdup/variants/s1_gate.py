A=' swept=(!skip).then(||sweep(&ctx,holder_key)).transpose()?.unwrap_or(0);fn sweep('
V={
 'v_if':[(A,' swept=if skip{0}else{sweep(&ctx,holder_key)?};fn sweep(')],
 'v_okq':[(A,' swept=if skip{Ok(0)}else{sweep(&ctx,holder_key)}?;fn sweep(')],
 'v_ifn':[(A,' swept=if !skip{sweep(&ctx,holder_key)?}else{0};fn sweep(')],
 'v_match':[(A,' swept=match (!skip).then(||sweep(&ctx,holder_key)){Some(Ok(v))=>v,Some(Err(e))=>return Err(e),None=>0};fn sweep(')],
}
