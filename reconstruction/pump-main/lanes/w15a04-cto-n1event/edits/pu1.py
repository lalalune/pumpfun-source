exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a04-cto-n1event/e/_n1.py').read())
EDITS=N1+[
("let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;let pargs=(target,a.bonding_curve.is_holder_reward,fee);","let pargs=(target,a.bonding_curve.is_holder_reward,fee);let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;"),
]
