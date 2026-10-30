# w13a42-cto-entrycopy3, wave-14 continuation: gene and boolean-spelling screens on five mains (no landing)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Wave 13 landed #3155 (0.62103 -> 0.62403); see `NOTES.md`. This continuation started on main 53abf28 (0.62672) and
followed main through 769f331 (0.63241), cef0574 (0.63421), f8dc901 (0.63481) and b174038 (0.63571).

Every number here comes from the raw-IR capture + rx `opt`/`llc` oracle (`tools/capvar.sh` + `rx.py`). On every base the
unedited capture gave `eq_main: true`, so the oracle tokens equal a `measure.sh` build. Ledger keys:
`0x22a10-w14-<main7>-entrycopy3-<trial>-v1`, approach `entrycopy3-genescreen`, about 350 rows.

**Result: no zero-loss gain landed.** My one measured improvement, m1 = `n_cb_rev` + `e_cb_local` + `e_reset`, was
superseded before I could open its PR. It built as 0.62762 / 3,281 slots at 27,400 B on 53abf28, with 1034/1034 and no
losses. stitch9 #3200 landed the same `n_cb_rev` head with other partners (0.62882).

## 1. Entry-copy angle: closed

- The original's 1/7/8/8/9 entry pieces of `new` come from validate's by-value `Result<Pubkey>` overlay (w13a41 #3160).
  Every faithful form costs 0.05-0.07 in register allocation (`NOTES.md`; w13a41 t8/t22).
- The only part of the angle that pays is the copy position: `args=&(new,)` after the CtoState literal. That is #3155,
  now on main. Removing the copy (n1-n3) costs 0.055.
- `args=(new,)` by value and `args=&new` both reduce to "no copy" (0.56885).

## 2. Single-gene screens (genes30 `g:`, w13a34 knobs `k:`, new entry spellings `x:`, regroupings `r:`)

| base | genes | above main |
| --- | ---: | --- |
| 53abf28 (0.62672) | 114 | `n_cb_rev`/`n_cb_if`/`cb_band` 0.62772 @27,392; `w_rl`/`w_rref` 0.62691 @27,384. #3200 has since landed both |
| 769f331 (0.63241) | 36 | none |
| cef0574 (0.63421) | 16 | none |
| f8dc901 (0.63481) | 13 | `r_co_dm` 0.63546 @27,320 (-80 B) |
| b174038 (0.63571) | 3 | none (`r_co_dm` 0.63426 @27,320) |

The new spelling families, all semantics-preserving and keeping the newline count:

- `autoswap.py` (769f331): operand swaps of all 16 simple `==`/`!=` comparisons outside #3215's. The byte-neutral
  swaps are 0 to -0.0009. The 3 `hopt==Some(true)` swaps give -0.056 at 27,168 B.
- `autoneg.py` (cef0574): `a==b` -> `!(a!=b)`. Byte-identical at 14 of 17 sites (folded). The losers are
  `t==*sharing` and the `current_creator.owner` test (-0.027 each) and `holder_creator_vault.key()!=dest`
  (-0.34 at +120 B).
- `genes42b.py` boolean regroupings: De Morgan (`!(a||b)`), parenthesisation (`a&&(b&&c)`) and non-short-circuit
  `&`/`|`.
  - Every `&`/`|` form loses 0.03-0.11.
  - Parenthesised and De Morgan forms are byte-identical, with three exceptions:
    - `ch_shpar`: `shared` as `A&&(B&&C)`. +8 B, -0.0001 on 769f331 and cef0574, -0.0001 on f8dc901. **The most neutral
      +8 B filler found.**
    - `r_co_dm`: collect_old as `!(st.holder_reward||st.creator==Pubkey::default())`. -56 B on 769f331/cef0574
      (-0.0005/-0.0002), then -80 B on f8dc901 (+0.00065), then -80 B on b174038 (-0.00145).
      **This is a global register-allocation lever, like `ev_reset_shared`, not a local size knob.** Re-screen it on
      each main. The same form with the operands swapped (`co_dm2`) keeps 27,400 B and cuts slots_diff from 3,178 to
      2,856, but the ratio drops to 0.58.
    - `ch_shkref`: `a.sharing_config.key==&a.bonding_curve.creator`. -80 B, -0.0015 on cef0574.
- Spellings of collect_old (`if`, `match`, `then`, `.ne()`) and of quote_locked (`iter().any`, a global binding, regrouped
  `||`, the `if` form) are byte-identical to main. `to_bytes()!=[0;32]` gives +96 B / -0.10. Reference forms give
  -232 B / -0.032. Native-first gives -0.0021 and whitelist-first -0.0033.

## 3. Size-balanced sets (all at 27,400 B, all below main)

- 53abf28: 12 pairs and triples. Best `n_cb_rev+e_cb_local+e_reset` 0.62762 (the m1 build above), then
  `n_cb_rev+c_fee_unwrap` 0.62732.
- 769f331: 32 sets of the 12 size genes (±8/16/24/32). Best `e_reset|s_su_iflet + e_cb_local|ev_cb_local` 0.63182
  (-0.0006).
- cef0574: 28 sets built around `r_co_dm`/`ch_shkref`. Best 0.63002.
- f8dc901: `r_co_dm` plus +80 B fillers, 20 sets. Best at 27,400 is `x_cp_inline+pu_band` 0.62882. With the pool-owner key
  (`*a.pool.owner==a.pump_amm.key()`, +80 B) it gives 0.63322, and 0.63202 on b174038.
- **The near-neutral +bytes filler is the scarce resource.** On cef0574 and later, the only fillers within 0.0011 of
  main are `ch_shpar` (+8, -0.0001) and `wl_ts_clockvar` (+16, -0.0011). Every +32..+80 filler costs 0.002-0.005.
  Shrinking gains (`scu_bs` -56 B, `r_co_dm` -80 B, outline306 -480 B) cannot be repaid without a loss.

## Next ideas

- Re-screen `r_co_dm` on each new main. When it is positive at -80 B, pair it with a positive +80 B change, such as a
  faithful by-value or entry-copy form that is positive in its own right. Padding with catalog fillers does not work.
- Use `ch_shpar` as the +8 B partner of any -8 B gain.
- A source-level search for +bytes fillers in the tail (event/pool CPI region), where w13a34 found effects to be local, is
  the missing tool for every shrinking gain.

## Tools (`tools/`)

- `genes42.py`: entry spellings (`x:`).
- `genes42b.py`: regroupings, collect_old and quote_locked spellings, tail fillers (`r:`).
- `autoswap.py` / `autoneg.py`: generators for comparison swaps and negations.
- `mkc.sh name gene...`: writes a capvar EDITS file combining genes from `g:`/`k:`/`x:`/`r:`.
- `run2q.sh`: runs `q0.txt`/`q1.txt` on two capvar slots.
- `bulkrec.py`: ledger recorder, using `B=<main7> MAIN=<ratio>` env.
