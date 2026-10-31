exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a04-cto-n1event/e/_n1.py').read())
EDITS=N1+[
("let (old_creator,old_fee)={","let (old_creator,old_fee,hr)={"),
("curve.is_holder_reward=holder.unwrap_or(false);","let hr=holder.unwrap_or(false);curve.is_holder_reward=hr;"),
(" (old_creator,old_fee)};"," (old_creator,old_fee,hr)};"),
("let pargs=(target,a.bonding_curve.is_holder_reward,fee);","let pargs=(target,hr,fee);"),
]
