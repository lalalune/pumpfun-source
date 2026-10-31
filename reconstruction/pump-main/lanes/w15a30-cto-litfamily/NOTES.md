# w15a30-cto-litfamily: literal init-order family screen (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B. Base main 9120883a9 (admin_cto source unchanged since
86e2a6b74, #3666): ratio 0.67376, 3,124 slots, M 2,249, Mperm 2,292. Continues w15a01-cto-devolfill next idea 3
(#3666 landed `fee_configurable` first in the CtoState literal, +1 M). Wave-15 lane continued in wave 16.
Ledger approach `litfamily`, keys `0x22a10-w15-9120883-litfamily-<variant>-v1`.

M is the count of matched masked tokens from the raw-IR oracle (`tools/scr.py`: rsync crate copy, permute one or more
literals with `tools/lit.py`, `capraw.py` identity capture with `-C no-prepopulate-passes`, `rx.py` opt -O3 + llc,
SequenceMatcher against the original). `eq_main` means the oracle tokens equal the landed baseline build.
ratio = 2M/(6676+(bytes-27400)/8). Mperm is the spill-slot relabel bound (`relab.py` via `tools/mperm.py`).

## Result

Interim (screen still running): no literal order beats main. 166 single-literal variants priced on main 9120883; the
best are byte-identical to main or tie it. One faithful tie: `b5:10234567` (sharing-CPI `event_authority` clones
`lamports` before `data`, as the original does) gives M 2,249 / Mperm 2,292 at 27,400 B with 4 slots changed.

## Family table (single moves on main 9120883)

| literal | variants | eq main | at 27,400 B | best M (dM) | best variant | bytes of best |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| pool | 13 | 0 | 0 | 2114 (-135) | `pool:6012345` | 27496 |
| cev | 7 | 4 | 4 | 2249 (+0) | `cev:2013` | 27400 |
| ev | 25 | 13 | 15 | 2249 (+0) | `ev:4012356789abc` | 27400 |
| shc | 13 | 0 | 2 | 2219 (-30) | `shc:0123465` | 27432 |
| wcr | 11 | 0 | 0 | 2236 (-13) | `wcr:501234` | 27480 |
| scr | 11 | 0 | 0 | 1332 (-917) | `scr:102345` | 27456 |
| ccf | 15 | 0 | 0 | 2245 (-4) | `ccf:70123456` | 27448 |
| tcf | 23 | 0 | 4 | 2156 (-93) | `tcf:0123456789ba` | 27384 |
| st | 16 | 2 | 9 | 2249 (+0) | `st:01234657` | 27400 |
| b5 | 1 | 0 | 1 | 2249 (+0) | `b5:10234567` | 27400 |
| b6 | 1 | 0 | 1 | 2244 (-5) | `b6:20134567` | 27400 |

Literal keys (`tools/lit.py`): `st` CtoState; `ev` AdminCtoEvent; `cev` CollectCreatorFeeEvent; `pool` AdminCtoPool CPI
accounts; `shc` AdminCtoSharingConfig CPI accounts; `tcf` TransferCreatorFeesToPumpV2 CPI accounts; `ccf`
CollectCoinCreatorFee CPI accounts; `wcr`/`scr` associated-token Create (wallet / sweep); `a1`..`a4` the TCF AccountInfo
literals (CpiContext program, coin_creator_vault_ata, pump_creator_vault_ata, program); `b1`..`b6` the sharing-CPI
AccountInfo literals (pool_authority, authority, global, mint, event_authority, program). A tag lists the original field
indices in their new order (`st:01234657` swaps fields 5 and 6).

- **CPI account structs** (`pool`, `shc`, `tcf`, `ccf`, `wcr`, `scr`): every move loses (-4 to -917 M) and most change the
  size. Their field orders fix the Rc-clone order of the `to_account_info()` calls, and main's orders already reproduce
  the original's clone order (map below), so these literals are pinned by the original, not free knobs.
- **Event literals** (`ev`, `cev`): 17 of 32 moves are byte-identical to main; the rest lose. Moving `timestamp`
  (the `Clock::get()?` call) or a key/creator load across others is what changes code; the plain field loads are scheduled
  independently of literal order.
- **CtoState** (`st`): `fee_configurable` must stay first (every other position is -1, the pre-#3666 code); moving
  `creator` loses 600+ M; bool-group swaps are byte-identical or lose.

## Rc-clone order map (new tool `tools/rcorder.py`)

Each `AccountInfo` clone in execute is an Rc strong-count increment (`ldxdw rP,[rA+0x8|0x10]; ldxdw rX,[rP]; add64 rX,1;
jeq rX,0`). The map lists every clone as (accounts-struct offset of the AccountInfo, lamports|data) for the original and
for a candidate. On main 9120883 all 42 increments line up one-to-one with the original **except three AccountInfos whose
literal clones `data` before `lamports`, while the original clones `lamports` first**:

| accounts offset | field | main literal | original |
| --- | --- | --- | --- |
| +0x48 | `creator_vault_quote_token_account` (TCF `pump_creator_vault_ata`, `a3`) | key, **data**, owner, **lamports**, ... | lamports, (key), data |
| +0xa0 | `pump_fees_event_authority` (sharing CPI `event_authority`, `b5`) | **data**, **lamports**, key, ... | lamports, (key), data |
| +0x98 | `pump_fees` (sharing CPI `program`, `b6`) | **data**, key, **lamports**, ... | lamports, data |

Faithful lamports-first screen (raw-IR oracle, main 9120883):

| variant | change | bytes | M | dM | note |
| --- | --- | ---: | ---: | ---: | --- |
| lfb5 | `b5:10234567` (event_authority lamports, data, key, ...) | 27,400 | 2,249 | 0 | tie; 4 slots differ (0x4370/0x4418 clone order now matches, 0x4670/0x4680 reload pair swaps); Mperm 2,292 = main |
| lfb6 | `b6:20134567` (program lamports, data, key, ...) | 27,400 | 2,244 | -5 | Mperm 2,287 |

w15a24 (#3736) already priced `a3` lamports-first on this main: 0.63074 @ 27,440 (data via `a.cvqta`) and 0.66457 @ 27,392
(natural derive order). The three data-first literals are compensations that earlier lanes kept because they score higher
on main's skeleton, not the original's spelling.

## Entry (CtoState build) observation

In the original the curve bools (`is_holder_reward` +0xa3, `is_cashback_coin` +0xa5, `is_mayhem_mode` +0xa2) are loaded
right after the global pointer and before the `quote_mint` copy and its three comparisons (orig 0x288-0x2b0); the global
fields (`max_configurable_creator_fee_bps` +0x430, `is_holder_reward_enabled` +0x43f, `creator_fee_configurable` +0x43e)
follow the whitelist `contains` call (orig 0x428-0x438), and the creator copy into `st` runs ascending
(`[bc+8]..[bc+0x20]` into `-0x38..-0x20`, orig 0x468-0x4a0). Main loads `fee_configurable`, copies the creator descending,
then loads the globals and the curve bools after `quote_locked`. Hoisting the curve bools before `quote_locked` is the
flaghoist lead that w14a106 (earlyload) and w15a28 (flaghoistrepay, #3746) already bounded below main; no literal order
can reproduce it because `quote_locked` is computed before the literal.

## Mperm of the 27,400 B screen variants

All below main's 2,292: tcf 3012.. 2,203; tcf 6012.. 2,180; tcf b01.. 2,156; tcf 0234..1 2,037; shc 6543210 2,187;
shc 0134562 2,216; ev ..abc3 2,268; ev ..abc2 2,245; st 10234567 (pre-#3666 order) 2,291. No literal order hides a better
skeleton behind a worse colouring.

## Tools (all experiment-only, under `tools/`)

- `lit.py`: literal locator/permuter for admin_cto.rs (19 literal keys; keeps line count).
- `scr.py`: spec-driven literal screen (crate copy, permute, capraw, rx, M, ledger row per variant).
- `mperm.py`: batch M / Mperm (spill relabel bound) for rx outputs.
- `rcorder.py`: Rc-clone order map, original vs candidate.
- `rx.py`, `capraw.py`, `relab.py`, `insmatch.py`: copied from w14a109 / w15a08 / w15a01 for reproducibility.
