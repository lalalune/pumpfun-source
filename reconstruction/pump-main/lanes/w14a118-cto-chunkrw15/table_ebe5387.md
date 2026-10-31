| orig chunk | tok | M_oo | rM_oo | fM_oo | sk_oo | region | owner |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 0x0000 | 62 | 35 | 29 | 22 | 23 | validate | validate head (w14a104/107/112/113) |
| 0x0200 | 62 | 24 | 17 | 34 | 25 | validate | validate head (w14a104/107/112/113) |
| 0x0400 | 64 | 60 | 41 | 56 | 29 | validate | validate head (w14a104/107/112/113) |
| 0x0600 | 58 | 24 | 21 | 18 | 9 | validate | validate head (w14a104/107/112/113) |
| 0x0800 | 60 | 16 | 16 | 12 | 27 | validate | validate head (w14a104/107/112/113) |
| 0x0a00 | 60 | 25 | 25 | 60 | 32 | validate | validate head (w14a104/107/112/113) |
| 0x0c00 | 64 | 37 | 36 | 64 | 26 | validate | validate head (w14a104/107/112/113) |
| 0x0e00 | 60 | 44 | 44 | 14 | 39 | validate | validate head (w14a104/107/112/113) |
| 0x1000 | 62 | 30 | 29 | 40 | 24 | validate | validate head (w14a104/107/112/113) |
| 0x1200 | 58 | 13 | 9 | 55 | 3 | validate | validate head (w14a104/107/112/113) |
| 0x1400 | 61 | 30 | 28 | 27 | 21 | validate | validate head (w14a104/107/112/113) |
| 0x1600 | 58 | 9 | 5 | 8 | 0 | validate | validate head (w14a104/107/112/113) |
| 0x1800 | 64 | 42 | 40 | 23 | 22 | validate join, tuple/target copy |  |
| 0x1a00 | 61 | 15 | 14 | 12 | 7 | prepare_bonding_curve, 410 |  |
| 0x1c00 | 59 | 11 | 7 | 11 | 4 | sweep head: dest PDA, 648 |  |
| 0x1e00 | 62 | 7 | 4 | 6 | 2 | sweep: dest PDA, amm_present |  |
| 0x2000 | 60 | 11 | 9 | 11 | 4 | sweep: amm frozen/raw amount, 719? |  |
| 0x2200 | 60 | 4 | 2 | 4 | 1 | sweep: 648 ConstraintSeeds |  |
| 0x2400 | 61 | 9 | 7 | 9 | 3 | sweep: 660 / frozen |  |
| 0x2600 | 63 | 21 | 13 | 20 | 5 | TCF head + clone run |  |
| 0x2800 | 64 | 15 | 5 | 14 | 2 | TCF clone run |  |
| 0x2a00 | 64 | 16 | 8 | 12 | 1 | TCF clone run |  |
| 0x2c00 | 64 | 22 | 7 | 17 | 0 | TCF clone run |  |
| 0x2e00 | 64 | 23 | 10 | 18 | 2 | TCF clone run |  |
| 0x3000 | 64 | 36 | 16 | 34 | 7 | TCF clone run |  |
| 0x3200 | 64 | 41 | 7 | 40 | 3 | TCF clone run |  |
| 0x3400 | 64 | 13 | 8 | 8 | 2 | TCF clone run |  |
| 0x3600 | 64 | 8 | 8 | 0 | 0 | TCF clone run |  |
| 0x3800 | 64 | 6 | 3 | 3 | 0 | TCF clone run |  |
| 0x3a00 | 64 | 15 | 12 | 8 | 4 | TCF call, Rent::get |  |
| 0x3c00 | 63 | 25 | 17 | 19 | 9 | sharing CPI clones | sharing CPI clone run (w14a114) |
| 0x3e00 | 64 | 31 | 36 | 26 | 36 | sharing CPI clones | sharing CPI clone run (w14a114) |
| 0x4000 | 64 | 34 | 30 | 27 | 34 | sharing CPI clones | sharing CPI clone run (w14a114) |
| 0x4200 | 64 | 33 | 22 | 26 | 54 | sharing CPI clones | sharing CPI clone run (w14a114) |
| 0x4400 | 64 | 54 | 43 | 57 | 35 | sharing CPI clones | sharing CPI clone run (w14a114) |
| 0x4600 | 64 | 27 | 20 | 16 | 1 | sharing CPI clones | sharing CPI clone run (w14a114) |
| 0x4800 | 64 | 26 | 26 | 0 | 0 | sharing CPI tail |  |
| 0x4a00 | 63 | 19 | 7 | 15 | 4 | sharing call, curve store | curve store (w14a91) |
| 0x4c00 | 63 | 7 | 6 | 6 | 5 | pool test + pool CPI clones | curve store (w14a91) |
| 0x4e00 | 64 | 13 | 5 | 13 | 3 | pool CPI call, Clock | curve store (w14a91) |
| 0x5000 | 62 | 11 | 2 | 9 | 1 | event data / emit | curve store (w14a91) |
| 0x5200 | 61 | 3 | 2 | 3 | 1 | emit_cpi invoke |  |
| 0x5400 | 63 | 16 | 5 | 15 | 2 | cold: ProgramError exits |  |
| 0x5600 | 55 | 4 | 4 | 0 | 0 | cold: error fmt |  |
| 0x5800 | 63 | 6 | 4 | 6 | 3 | cold: 284/556, native Rent |  |
| 0x5a00 | 63 | 20 | 15 | 11 | 1 | cold: native ensure_rent/transfer |  |
| 0x5c00 | 64 | 22 | 6 | 21 | 0 | cold: wallet token_frozen, coin clones |  |
| 0x5e00 | 64 | 9 | 8 | 8 | 4 | cold: create_idempotent x2 |  |
| 0x6000 | 64 | 14 | 9 | 12 | 4 | cold: transfer_vault_tokens, collect |  |
| 0x6200 | 64 | 20 | 16 | 18 | 4 | cold: Clock, frozen |  |
| 0x6400 | 62 | 11 | 2 | 9 | 0 | cold: collect event emit |  |
| 0x6600 | 61 | 14 | 8 | 7 | 0 | cold: collect emit_cpi |  |
| 0x6800 | 64 | 8 | 3 | 6 | 1 | cold: coin fee CPI clones |  |
| 0x6a00 | 33 | 3 | 1 | 3 | 0 | cold: collect_coin_creator_fee |  |
| total | 3,325 | 1,092 | 777 | 993 | 529 | | |
