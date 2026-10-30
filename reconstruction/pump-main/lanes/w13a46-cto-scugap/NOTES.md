# w13a46-cto-scugap (wave 13)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: land the skip-first skip-tree tuple (`t_scu`, w13a08 #2975 / w13a30 #3138) by filling its size gap.

## Result 1 (main 52c0b087c, 0.62103)

`t_scu` alone on 52c0b087c: 27,344 B / 0.62708 (+0.0061, -56 B). `t_usc`: 27,360 / 0.62659.

Filled with two tail knobs from the w13a34 catalog (#3137), which are local to the post-update tail:
- `pool_hr_local`: the pool CPI's `is_holder_reward` argument is the `holder` local (the curve was just set to it).
- `ev_nf_pre`: the event's `new_creator_fee_bps` is read into `nf` before `pool_updated` (the pool CPI cannot write
  the Pump-owned curve).

| metric | main 52c0b087c | this |
| --- | ---: | ---: |
| admin_cto bytes | 27,400 | 27,400 |
| ratio | 0.62103 | **0.62552** |
| slots_diff | 3,306 | 3,302 |
| normalized / raw | 1034 / 1034 | 1034 / 1034 |
| gains / losses | | 0 / 0 |
| runtime differential | | 363 cases, 0 mismatches |

Ledger: approach `scugap-filler`, keys `0x22a10-w13-52c0b08-scugap-<trial>-v1`.
