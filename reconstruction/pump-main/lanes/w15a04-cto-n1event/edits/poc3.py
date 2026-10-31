exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a04-cto-n1event/e/_n1.py').read())
exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a04-cto-n1event/e/_po.py').read())
EDITS=N1+PO+[("let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;","let old_creator=curve.creator;"),("  curve.is_cashback_coin=cashback;\n","  curve.is_cashback_coin=cashback;let old_fee=curve.creator_fee_bps;\n")]
