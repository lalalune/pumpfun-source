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

## Wave 14 continuation (mains 53abf28b1 -> 308b545f1 -> cef0574cf): no landable gain

PR #3153's source (Result 1) conflicted with #3155/#3168 and was superseded: main took `n_cb_rev`, `w_rl`, `ev_nf_pre`
and `p_empty_first` itself (#3200, #3207). The branch now equals main in `programs/`; this section is notes only.
All numbers are `measure.sh` at the built size. Ledger: approach `scugap-filler`,
keys `0x22a10-w13-{53abf28,308b545,cef0574}-scugap-*` (about 330 rows this wave).

### 1. Skip-first still gains, but only with `args` back before `CtoState`

#3155 (entrycopy3) moved `let args=&(new,)` to after `cashback`. With args there, every skip-before-collect_old
tuple order (scu, suc, usc) collapses to **0.48 at 27,392 B**. This is code shape, not frame: with every r10 load/store
offset masked (`tools/fm.py`, cef0574) main is 0.68544, T_scu args-early 0.68616, collapsed T_scu 0.48165. Moving `args` to just before
`let st=CtoState{` (or just before the block: identical) undoes the collapse:

| main (ratio) | `T_scu A4_bs` | `T_usc A4_bs` | deferred `let (skip,collect_old,sharing_update);` (args unmoved) |
| --- | --- | --- | --- |
| 53abf28 (0.62672) | 0.62918 @ 27,344 | 0.62779 @ 27,360 | |
| 308b545 (0.63062) | 0.63308 @ 27,344 | 0.63169 @ 27,360 | 0.63033 @ 27,424 |
| cef0574 (0.63421) | **0.63578 @ 27,344** | 0.63529 @ 27,360 | 0.63393 @ 27,424 |

- Other `args` placements with T_scu: top of execute 0.548, before quote_locked 0.539, before holder_key 0.541,
  after `sk` 0.6262 @ 27,368 (308b545), after validate 0.570 (6ff770f).
- Deferred-init form: only the **let-pattern order** matters. All 36 let x assignment orders give two builds:
  skip before collect_old 0.63033 @ 27,424, collect_old before skip 0.4812 @ 27,392 (collapse). Nesting
  `(skip,(collect_old,sharing_update))` gives the same split.

### 2. The 56 B gap has no cheap filler: the gain per byte is smaller than every filler's cost per byte

The skip-first gain is +0.0025 on 53abf28/308b545 and +0.0016 on cef0574, for -56 B. A filler is only useful below
about 0.00003-0.00004 ratio per byte. Single-knob screens over the whole catalog (genes30 + w13a34 knobs, 101 on
T_scu+args-early+P_hr at 53abf28, 88 on T_scu+args-early at 308b545, 66 on the deferred form) give these size-ups
(delta vs the skip-first base at 308b545):

| knob | bytes | ratio cost |
| --- | ---: | ---: |
| `k_wl_ts_clockvar` (wallet event Clock local) | +16 | -0.0005 (the only one cheap enough) |
| `N4_cb` (cashback back to `st.cashback&&!holder`) | +8 | -0.0016 |
| `e_cb_local` | +8 | -0.0019 |
| `x_cp_inline` | +16 | -0.0020 |
| `U4_keyfn` (`*a.pool.owner==a.pump_amm.key()`) | +80 | -0.0031 |
| `P_hr` (pool CPI `holder` from the local) | +24 | -0.0057 |
| `k_cu_fee_oldunwrap`, `c_fee_unwrap`, `x_ata_rev` | +8 | -0.004..-0.005 |

The size-downs are all ratio-negative on the skip-first base (`e_reset`/`s_su_iflet`/`x_co_then` -8 B at -0.0014,
`E4_nf_back` -24 at -0.0021, `k_sh_prog_let` -32 at -0.003). Costs add up close to linearly. Best 27,400 B fills:

| main | fill | ratio | main |
| --- | --- | ---: | ---: |
| 53abf28 | T_scu args-early + U4_keyfn + w_rl + n_cb_rev (r1) | **0.62932** (+0.0026; superseded by #3200 before landing) | 0.62672 |
| 308b545 | T_scu args-early + U4_keyfn_of + E4_nf_back | 0.62932 | 0.63062 |
| cef0574 | T_scu args-early + U4_keyfn_of + E4_nf_back | 0.63202 | 0.63421 |
| cef0574 | deferred skip-first + E4_nf_back | 0.63122 | 0.63421 |

r1 was zero-loss (1034/1034) and passed the 363-case differential on 53abf28, but main moved to 308b545 (+0.0039,
using two of r1's own knobs) before it could land.

### 3. Insertion census (orig vs T_scu args-early, `tools/census.py`)

Against the original, the skip-first build has 55 original-only and 102 candidate-only instructions, in runs of at most
13. The largest original-only run (13 insns at orig 0x290) is the early curve-bool loads: the original reads
`is_cashback_coin` [+0xa3], `is_holder_reward` [+0xa5] and `is_mayhem_mode` [+0xa2] **before** the inlined
global_quote memcmps and spills two of them (`[r10-0x8e8]`, `[r10-0x8e0]`). Every source form of that
(bools into locals before `quote_locked`, in any of 3 orders or as one tuple) costs +168 B and ~-0.05 (0.5755).
That matches the w12/w13a41 results (t20-t29). The rest are 1-8 instruction spill/reload and register-copy runs in the clone run and
the sweep (0x4978: the CPI clone stores reload 3 spilled bytes the original kept). The 56 B are distributed RA code,
not a missing statement, so no faithful-data-flow statement fills them.

### Next ideas (untried)
- A *new* filler class with cost < 0.00003/B. Only Clock/Rent-local forms reach it so far; look for other sysvar or
  by-value copies on cold paths (wallet / native sweep).
- (checked, dead) The collapsed builds are not "original shape, wrong frame": frame-masked they score 0.4817.
- What the collapse moves (`tools/cc.py` s5 vs c5 on cef0574): one 755-instruction run, the wallet body from the
  `token_frozen(creator_vault_quote_token_account)` call (`ldxdw r2,[r8+0x88]`, good build +0x2438) on, is placed
  after the sweep (+0x3de8) instead of inline. That is MachineBlockPlacement relaying out the collect_old arm. Next: find
  which branch weight or phi makes the args-copy position and the
  skip-first phi order interact (w13a31 `bwfm.py` on the collect_old gate). That could give the skip-first gain without moving `args`, and so without the 56 B gap.
