# coin gate tests do_coin only (orig form 'if do_coin{'), IR level
EDITS=[("  %_123.i78 = and i1 %do_coin.sroa.0.1.off061.i, %coin_present.i\n  br i1 %_123.i78,","  br i1 %do_coin.sroa.0.1.off061.i,")]
