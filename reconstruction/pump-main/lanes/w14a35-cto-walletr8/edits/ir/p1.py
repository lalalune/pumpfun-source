# pin do_coin to r8 at the coin gate (bound only)
EDITS=[("""  %_123.i78 = and i1 %do_coin.sroa.0.1.off061.i, %coin_present.i
""","""  %pz = zext i1 %do_coin.sroa.0.1.off061.i to i64
  call void asm sideeffect "", "{r8}"(i64 %pz)
  %_123.i78 = and i1 %do_coin.sroa.0.1.off061.i, %coin_present.i
""")]
