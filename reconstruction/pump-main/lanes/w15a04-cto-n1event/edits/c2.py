exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a04-cto-n1event/e/_n1.py').read())
EDITS=N1+[
(" let (old_creator,old_fee)={\n  let curve=&mut ctx.accounts.bonding_curve;let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;"," \n  let curve=&mut ctx.accounts.bonding_curve;let old_creator=curve.creator;                                  "),
("  curve.is_cashback_coin=cashback;\n","  curve.is_cashback_coin=cashback;let old_fee=curve.creator_fee_bps;\n"),
(" (old_creator,old_fee)};\n"," \n"),
]
