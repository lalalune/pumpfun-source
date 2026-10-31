exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a04-cto-n1event/e/_n1.py').read())
EDITS=N1+[("let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;","let pool:&AccountInfo=&a.pool;let pool_updated=pool.owner==&AMM && !pool.data_is_empty();"),("pool:a.pool.to_account_info(),pool_authority:a.pool_authority","pool:pool.clone(),pool_authority:a.pool_authority")]
