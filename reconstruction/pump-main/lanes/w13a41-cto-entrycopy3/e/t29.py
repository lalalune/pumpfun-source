exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a41-cto-entrycopy3/e/common.py').read())
B='let (cb0,hr0,my0)=(a.bonding_curve.is_cashback_coin,a.bonding_curve.is_holder_reward,a.bonding_curve.is_mayhem_mode);'
L=stl(['creator','max_fee','mayhem','holder_reward','cashback','quote_locked','holder_enabled','fee_configurable']).replace('mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin','mayhem:my0,holder_reward:hr0,cashback:cb0')
EDITS=T8+[(QL,B),(STL,L+ARGS)]
