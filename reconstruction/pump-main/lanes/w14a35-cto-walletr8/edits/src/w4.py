# swept bound where produced into a (swept,skip) tuple
EDITS=[(" swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);"," swept=match (!skip).then(||sweep(&ctx,&holder_key)){Some(r)=>r?,None=>0};")]
