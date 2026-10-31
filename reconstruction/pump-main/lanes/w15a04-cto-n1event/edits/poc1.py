exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a04-cto-n1event/e/_n1.py').read())
exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a04-cto-n1event/e/_po.py').read())
EDITS=N1+PO+[
(" let (old_creator,old_fee)={\n  let curve=&mut ctx.accounts.bonding_curve;let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;"," \n  let curve=&mut ctx.accounts.bonding_curve;let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;"),
(" (old_creator,old_fee)};\n"," \n"),
]
