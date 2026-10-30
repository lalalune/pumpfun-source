# w14a14-cto-mf1fill: mf1 (max_fee by reference) plus faithful fill for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main cef0574cf (0.63421, 3,178 slots, 27,400 B). This lane continues w14a03-cto-liverange's open IR leads (#3210, #3228).
Ledger keys: `0x22a10-w14-cef0574-mf1fill-*-v1`.

**Result: one small zero-loss gain, 0.63421 -> 0.63481 at 27,400 B (3,173 slots).** It is `qlin2`, a source form of the
IR re-read lead `%_255` (section 3). The mf1 lead itself is dead. So are the other re-read leads, which were mostly size artifacts, and no catalog
fill pays for them.

## Landed candidate: qlin2

| | main cef0574 | qlin2 |
| --- | ---: | ---: |
| admin_cto ratio | 0.63421 | **0.63481** |
| slots_diff | 3,178 | **3,173** |
| bytes | 27,400 | 27,400 |
| M (matched original instructions) | 2,117 | 2,119 |
| normalized / raw | 1034 / 1034 | 1034 / 1034, 0 losses |
| differential | | 363 cases, 0 mismatches |
| unstripped sha16 | | 5b221a80bc1019ea |

```rust
// before
let quote_locked=crate::pump_quote::global_quote(a.bonding_curve.quote_mint,&a.global);
// after (global_quote's body, written out in execute)
let quote_locked={let q=a.bonding_curve.quote_mint;q==Pubkey::default()||q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(&q)};
```

Mechanism:
- With the call, `&a.global` is coerced to `&Global` at the call site. The Global box pointer (accounts+8) is then loaded once,
  before the two memcmp tests, and stays live into the CtoState literal.
- Written out, the deref happens only on the `contains` path. The CtoState literal (max_fee, holder_enabled, fee_configurable)
  has no dominating load, so it reloads the box pointer. GVN's load PRE does not insert into two predecessors.
- The result equals the w14a03 IR re-read oracle's `%_255` variant token for token (0.63481, 27,400 B). The gain is the
  entry register assignment: the accounts pointer goes to r8, as in the original (orig 0x22a38 `ldxdw r8, [r2+0x8]`).
- `qlin3` keeps the `global_quote` call as the third operand. It gives 0.58139 at 27,472 B.
- Ledger: `0x22a10-w14-cef0574-mf1fill-qlin2-v1`.

## 1. Judge off-pin trials by M, not by ratio

As w14a08 showed, `ratio = 2M / (3339 + n)`. Here M is the number of original instructions the candidate matches and
n is the candidate's instruction count (lddw counts as one; main has n = 3,337). Shrinking execute by 22 instructions
(176 B) raises the ratio by about 0.0035 even when M is unchanged. At 27,400 B the only way to beat main is M ≥ 2,118
(main M = 2,117). Every number below gives M. Where only bytes were known, n is estimated as bytes/8 − 88.

## 2. The mf1 lead is dead on cef0574

| trial (raw-IR oracle, w14a03 `capvar.sh`) | bytes | ratio | M |
| --- | ---: | ---: | ---: |
| main cef0574 (oracle reproduces it, eq_main) | 27,400 | 0.63421 | 2,117 |
| mf1 (`CtoState<'g>{..max_fee:&'g u64..}`, `f>*st.max_fee`) | 27,224 | 0.63270 | **2,105 (−12)** |
| best IR re-read on mf1 (global box pointer `%_255`) | 27,352 | 0.63328 | 2,112 |

- On 53abf28 mf1 showed +0.00157 at −184 B, which was mostly a size effect. After #3200, #3207, #3215 and #3210 even the raw ratio
  is −0.0015.
- mf1 does not give the original's register shape. The original stores the **value** of max_fee into st at `[r10-0x18]`
  (orig 0x22ee0 `stxdw [r10-0x18], r4`) and keeps it in r9 for the 338 test (orig 0x1658 `jlt r1, r9`). mf1 stores the
  **pointer** (`add64 r6, 0x430; stxdw [r10-0x18], r6`), still spills it (now the pointer, at -0x948), and adds a
  dependent load at the test. So it moves away from the original.
- The original has r9 free for max_fee because it copies `new`'s pieces at entry (entrycopy, owned by w13a42). This
  lane cannot reach that.

## 3. The other IR re-read leads, re-ranked by M (`data/irreM-base.tsv`, 205 variants)

| value | what | bytes | ratio | M |
| --- | --- | ---: | ---: | ---: |
| `%34` (global+1086) | **creator_fee_configurable**, not holder_enabled as w14a03's notes say (it feeds the line-334 test) | 27,224 | 0.63751 | 2,121 (+4) |
| `%_255` | Global box pointer (accounts+8), re-read in global_quote's contains-loop preheader and in the st block | 27,400 | 0.63481 | 2,119 (+2), 3,172 slots |
| `%_195.1.i` | collect_v2::collect Ok payload piece (quote_mint[0..8]), re-read after Clock::get | 27,264 | 0.63583 | 2,117 |
| `%28` / `%30` | curve is_holder_reward / is_cashback_coin | 27,312 | 0.635 | 2,116 / 2,115 |
| `%_28` | max_fee itself | 27,232 | 0.63441 | 2,111 |
| `ctx.accounts` per-block re-reads (`--sub %_246`, 38 blocks) | the pool_updated lead | 27,400-27,416 | ≤0.63382 | ≤2,116 |

- The original also loads fee_configurable at entry (orig 0x22e48 `ldxb r5,[r6+0x43e]`). It spills it to `-0x940`, exactly as
  main does (main 0x15a0 `ldxdw r1,[r10-0x940]`), so the %34 re-read is not a faithful direction either. Its +4 M is
  register-allocation side effects.
- `%_255` gains by swapping the accounts pointer into r8 at entry, as in the original. The original loads the box pointer once (0x22c98) and
  holds it in r6, so a reload is not the original's form. **`qlin2` expresses it in source and is the landed candidate.**
- Combinations (`tools/irrecombo.py`) are not additive: %34+%_195.1 2,124 @27,200; %_195.1+%_255 2,122; %34+%_255 2,118 @27,344;
  %34+%_195.1+%_255 2,119; %34+%30 2,077. That is ±7 M of RA noise. Apart from `%_255`, no re-read has a source form, because there is
  no clobber between the loads, so GVN folds every source re-read (as w14a03's gref showed). `%_255` works only because writing out
  `global_quote` removes the dominating load.

## 4. Fill screen (size-knob catalog on cef0574 and on mf1)

The 47 knobs of `$SWARM/w11/sizeknobs-cto.json` that still apply to cef0574, plus `if do_collect||collection_native` and
`pu_amm_keyfn` (now `*a.pool.owner==a.pump_amm.key()`), were screened singly on main. The positive-size ones were also screened on mf1.
`data/knobs-cef0574.tsv` has the full table.

| knob (single, on main cef0574) | bytes | ratio | M |
| --- | ---: | ---: | ---: |
| 7 knobs (L_share_none_first, ev_auth_deref, ev_ts_map, g_native_amount_ne, g_s7_ammif, g_s7_amtne, g_s7_tokamtne) | 27,400 | = main | 2,117 (byte-identical) |
| cu_replace / g_old_fee_first / g_canedit_first / g_s7_destrev | 27,400 | 0.6336-0.6339 | 2,115-2,116 |
| wl_ts_clockvar, g_w_clock_local | +16 | 0.63312 | 2,114 |
| `if do_collect\|\|collection_native` | +64 | 0.63196 | 2,112 |
| ev_cb_local | +8 | 0.63202 | 2,110 |
| pu_amm_keyfn (`*a.pool.owner==a.pump_amm.key()`) | +80 | 0.63108 | 2,110 |
| w_ev_creator_first | +64 | 0.62867 | 2,101 |
| fee_unwrap family (g_fee_unwrap, cu_fee_oldunwrap, L_fee_unwrap_again) | +8 | 0.62873 | 2,099 |
| ev_mint_key / g_s7_destscope / ev_nc_target | +16 / +96 / +56 | 0.625 / 0.546 / 0.384 | 2,087 / 1,825 / 1,284 |

| mf1 + fill | bytes | ratio | M |
| --- | ---: | ---: | ---: |
| mf1 + do_collect\|\|collection_native | 27,288 | 0.63224 | 2,106 |
| mf1 + wl_ts_clockvar / g_w_clock_local | 27,224 | 0.63240 | 2,104 |
| mf1 + ev_cb_local | 27,232 | 0.63201 | 2,103 |
| mf1 + pu_amm_keyfn | 27,304 | 0.63076 | 2,102 |
| mf1 + w_ev_creator_first | 27,288 | 0.62834 | 2,093 |

**Fill ceiling.** Every positive-size knob costs 3 to 830 matched instructions. The best mf1 composite reaches M 2,106 at 27,288 B,
11 below main and 112 B short. No catalog fill can bring mf1 back to the pin at M ≥ 2,118.

## 5. Other checks

- Block order: moving the 334 error block (`bb59.i`) next to the 338 error block (`bb66.i`), where the original has it (orig 0x1730),
  gives byte-identical output after `bb66.i` and 0.62723 @27,408 B before it. The cold-block chain is MachineBlockPlacement's choice,
  not IR order (`tools/blkmv.py`).
- The orig shared-arm block 0xd78-0xe58 reads st.creator back from the st stack copy (`[r10-0x30/-0x28/-0x20/-0x38]`) and stores
  it twice. Ours never reads st back, because GVN forwards it. No source form makes LLVM keep that st read while validate is inlined.
- The error payload is (r9, r7) at all 15 of the original's validate/exit error sites. In ours it is (r8, r7) at 11 sites. That is a
  register-assignment residual worth about 16 slots/tokens (tagreg/colderr lanes).

## Tools (experiment only, `tools/`; the lane reuses w14a03's capvar.sh/rx.py/irre.py)

| tool | what it does |
| --- | --- |
| `irre_k.py` | w14a03 `irre.py`, but keeps `m.o` when `KEEPO=1` |
| `irrecombo.py <m.ll> v1,v2,..` | applies several re-read variants together, runs llc, prints ratio/bytes/M |
| `mdiff.py <a> <b>` | M for two builds plus per-0x400 orig-bin matched-count deltas |
| `hunks.py <cand> lo hi <cand.dis>` | orig-vs-candidate diff hunks with disassembly text, score.py token masking |
| `blkmv.py <m.ll> <blk> <after-blk or BEFORE:blk>` | moves one IR block of execute (renumbers values) and runs llc + score |

## Next ideas (not this lane's)

- Anything that frees r9 in validate (entry copy of `new`, w13a42) is the only route to the original's max_fee register.
  mf1 is not that route.
- Payload register r9 vs r8 at the 15 error sites (tagreg).
