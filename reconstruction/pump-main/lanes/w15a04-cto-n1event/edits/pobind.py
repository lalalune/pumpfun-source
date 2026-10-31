exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a04-cto-n1event/e/_n1.py').read())
exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a04-cto-n1event/e/_po.py').read())
EDITS=N1+PO+[
("let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();","let pool:&AccountInfo=&a.pool;let pool_updated=pool.owner==&AMM && !pool.data_is_empty();"),
]
