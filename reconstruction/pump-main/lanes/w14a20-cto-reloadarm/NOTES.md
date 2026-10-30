# w14a20-cto-reloadarm: in-arm / after-clobber reload spellings for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: continue w14a14-cto-mf1fill (#3241 qlin2, #3246 notes): a source re-read becomes a real reload only when no load of
the same address dominates it, or when a store that may alias it sits in between.
Ledger keys: `0x22a10-w14-b174038-reloadarm-*-v1` and `0x22a10-w14-1b0ae70-reloadarm-*-v1` (approach `reloadarm-source`).

## Landed: #3267 (merge 7e6aa9caa). On 1b0ae70: 0.63661 -> 0.63930. After land.py merged #3272 (3f02a925e, 0.63871): 0.6414 (M 2,141), 0 losses, 363/0

The table below is the measurement on 1b0ae70, before the merge.

| | main 1b0ae70 | g1_ev_hr_curve |
| --- | ---: | ---: |
| admin_cto ratio | 0.63661 | **0.63930** |
| slots_diff | 3,173 | 3,174 |
| bytes | 27,400 | 27,400 |
| M (matched original instructions) | 2,125 | **2,134** |
| normalized / raw | 1034 / 1034 | 1034 / 1034, 0 losses |
| differential | | 363 cases, 0 mismatches |
| unstripped sha16 | | e0535b7613ed973d |

```rust
// sharing CPI, event_authority clone. before:
event_authority:{let x=&*a.pump_fees_event_authority;AccountInfo{lamports:x.lamports.clone(),data:x.data.clone(),key:x.key,owner:x.owner,..}}
// after: every field read through a.pump_fees_event_authority
event_authority:AccountInfo{lamports:a.pump_fees_event_authority.lamports.clone(),data:a.pump_fees_event_authority.data.clone(),key:a.pump_fees_event_authority.key,..}
// AdminCtoEvent. before: is_holder_reward:holder   after (the original's event form, orig 0x4fe0 ldxb [curve+0xa5]):
is_holder_reward:a.bonding_curve.is_holder_reward
```

Mechanism:
- **g1 is a real reload with a real clobber.** `lamports.clone()`/`data.clone()` store to the Rc strong counts. Those
  stores have no noalias metadata, so they may alias the accounts struct. A field read written as
  `a.pump_fees_event_authority.<f>` after the first clone therefore reloads the AccountInfo pointer (accounts+160).
  With the `x` binding, x stays one SSA value across the clones. g1 reproduces the IR re-read lead `%x20` (found on
  1b0ae70) token for token: M 2,130 at +8 B.
- `ev_hr_curve` (w12a13 size-knob catalog) repays the 8 B. The event reads `is_holder_reward` back from the curve, as the
  original does, instead of holding `holder` in a register (#3257 had switched it to `holder`). Together: M 2,134 at 27,400 B.
- The other hand-written clones (pool_authority, global, mint and the two sweep pump_amm clones) lose M when read
  this way in full (`irreM-1b0ae70.tsv`, `%x`, `%x18`, `%x19`, `%x.i`, `%x11.i`). Partial forms (only the reads after the
  first Rc clone) are in section 5.

## 1. Oracles re-run on b174038 (before #3257), ranked by M

w14a03's raw-IR capture (`capvar.sh` -> `capraw.py`) plus `rx.py` (opt -O3 + llc) reproduces main exactly (`eq_main`,
0.63571 / 27,400 B / M 2,122). `rx.py`, `irre.py`, `irhold.py` and `irremat.py` now also print M. Tables:
`irreM-b174038.tsv` (298 re-read variants), `irholdM-b174038.tsv` (84 hold variants), `irrematM-b174038.tsv` (38 remat variants).

| oracle | variants | above main (M > 2,122) |
| --- | ---: | --- |
| re-read (whole + per-block, `--sub`) | 298 | 3 (below) |
| hold (fold dominated reload into the first load) | 84 | none (best 2,119) |
| pure-value remat | 38 | none (best = main) |

| re-read lead | value | bytes | ratio | M | source form? |
| --- | --- | ---: | ---: | ---: | --- |
| `%_195.1.i` | collect Ok payload word quote_mint[0..8] at `_58.i+16`, re-read in the Clock::get block | 27,232 | 0.63892 | 2,126 | **Invalid.** The reload sits after `lifetime.end(_58.i)`. Stack coloring gives Clock::get's sret the same slot (r10-0x2d0), so the variant reads `[r10-0x2c0]` *after* Clock::get overwrote it (see `p195-excerpt.txt`, 0x61a8-0x61d8). The original (orig 0x61e0 `ldxdw r9,[r10-0x2c0]`) matches main here except for r9 vs r8. That is the payload-register residual that tagreg/colderr own. |
| `%33` | holder_enabled (global+1087), re-read at the line-296 test | 27,360 | 0.63709 | 2,125 | none: see section 2 |
| `%_363@bb1` | sharing_config AccountInfo pointer (accounts+144) re-read in the owner test | 27,408 | 0.63591 | 2,123 | none: no clobber between the loads, so the source re-read `a6`/`d7` is byte-identical. The original spills this pointer (`-0x8e0`, orig 0x150/0x210/0x258) because its r7 holds an entry-copy value. That is an RA consequence of the entry copy (w13a41/42), not a reload. |

The remaining re-reads at M 2,121 (max_fee `%_33`, fee_configurable `%35`, the event `nf`) are all below main.

## 2. Source spellings tried (raw-IR capture + rx oracle = build tokens)

| trial | spelling | bytes | ratio | M |
| --- | --- | ---: | ---: | ---: |
| main b174038 | | 27,400 | 0.63571 | 2,122 |
| a1 | `holder_enabled:holder==Some(true)&&a.global.is_holder_reward_enabled` (deref behind `&&`) | 27,592 | 0.47313 | 1,585 |
| a2 / a8 | `holder_enabled:holder!=Some(true)\|\|..` / `!(holder==Some(true))\|\|..` | 27,568 | 0.47275 | 1,583 |
| a3 | `holder_enabled:a.bonding_curve.is_holder_reward\|\|..` | 27,504 | 0.46255 | 1,547 |
| a10 | `holder_enabled:if holder==Some(true){..}else{false}` | 27,592 | 0.47313 | 1,585 |
| a4 | `fee_configurable:fee.is_none()\|\|a.global.creator_fee_configurable` | 27,464 | 0.47367 | 1,583 |
| a9 | `fee_configurable:fee.is_some()&&..` | 27,216 | 0.58861 | 1,958 |
| a5 | `max_fee:if fee.is_some(){a.global.max_..}else{0}` | 27,344 | 0.53231 | 1,775 |
| a6 | shared chain: owner read through a fresh `{let a=&ctx.accounts;..}` in the `&&` arm | 27,400 | = main | 2,122 |
| a7 | pool_updated: `ctx.accounts.pool.owner` in the `&&` arm | 27,400 | = main | 2,122 |
| b1 | CtoState literal with `quote_locked:` set to the qlin2 body inline (field order unchanged) | 27,312 | 0.58905 | 1,963 |
| b3 / b5 | same, with literal order creator,{mayhem,hr,cb \| cb,hr,mayhem},quote_locked,max_fee,he,fc | 27,352 | 0.61019 | 2,035 |
| b2 / b6 | same, bools first (original load order), creator last | 27,208 | 0.57336 | 1,907 |
| b7 | cb,hr,mayhem,quote_locked,creator,max_fee,he,fc | 27,368 | 0.57914 | 1,932 |
| c1 / c2 | validate takes `holder_key:Pubkey, sharing:Pubkey` by value; 312 holder-first / sharing-first | 27,328 | 0.56097 / 0.55887 | 1,870 / 1,863 |
| c4 | holder_key by value only, `t==holder_key\|\|t==*sharing` | 27,440 | 0.54752 | 1,829 |
| c5 | sharing by value only | 27,400 | 0.56171 | 1,875 |
| c3, c6, d1, d2, d5, d7 | see SUMMARY.json | | | |

Notes on the table:
- **Short-circuit or in-arm global reads in the CtoState literal (a1-a5, a8-a10) all add a conditional block to the entry
  chain** between the quote tests and validate. That changes the head's block frequencies and layout (the same ~0.47
  collapse w14a11 mapped for the sweep gate). The reload itself is never the issue. The source has no way to put the
  deref "in the arm" without making a new arm.
- In-arm re-reads that do not add an arm (a6, a7, d-series) are byte-identical. `ctx` is noalias, and nothing between
  the loads clobbers memory (memcmp is readonly), so GVN folds them. qlin2 worked only because writing out
  `global_quote` moved the first deref into an arm that already existed (the `contains` operand of an existing `||`).
- No other existing `||`/`&&`/if arm in execute holds the first deref of a value that is read again later. The other
  helpers take `&Account`/`&AccountInfo`, so no coercion happens at a call site. The account reads after
  `find_program_address`, `data_is_empty`, `prepare_bonding_curve` and the CPIs are already reloads (calls clobber).
- token_frozen / token_raw_amount inlined by hand would replace one internal call with that body's own calls
  (data_is_empty, try_deserialize), so the original's 154 internal call count could not hold. Not tried.

## 3. Direction check: the original reloads less from account memory, not more

Non-stack load multiset (`ldx* [rX+off]`, rX != r10), main vs original: main has **15 more**
(+0x8 51/47, +0x10 41/38, +0x18 49/46, +0x38 12/10, +0x20, +0x70, +0xa5 3/2). The original keeps 30 more stack reloads
(w13a50). So the general direction from main toward the original is *hold and spill*, not *re-read*. qlin2's gain came
from the register choice it caused (accounts pointer in r8), not from having an extra reload. One example is the extra
`ldxb r8,[r1+0xa5]` at main 0x4c18: the pool CPI's `a.bonding_curve.is_holder_reward`, which the original does not
reload. Its source forms (`pool_hr_local`, h2pair) are already in the ledger as losses.

## 4. Structural residuals seen while reading (for other lanes)

- Orig 0x0d78-0x0e58 (57 instructions, the biggest single unmatched hunk after the 0x420 head) is the post-validate
  `shared&&!holder` arm with `target=st.creator`, laid out as fallthrough after the line-312 memcmps. In main, the 312 success
  edge jumps far ahead (`jne r0,0,+0xe4` at 0xd00) and the error block is the fallthrough. In the IR, MemCpyOpt
  forwards the first 7 bytes of st.creator from the curve (`%23`) and reads the rest from `%st`. The original reads all
  four words back from st (-0x38..-0x20). This is block placement plus memcpy forwarding, not RA.
- Line 312 in the original compares t against a **copy** of holder_key (-0x518) first and a copy of the sharing key
  (-0x470) second. Main compares against sk (-0x518) first and holder_key (-0x6a0) second. All by-value spellings
  (c1-c5) lose 250-300 M. The copy must come from somewhere other than a by-value parameter.
- `tools/gaps.py <cand.o|.so> [n]` lists the largest unmatched orig/cand hunks (score tokens) with offsets. On main:
  M 2,122, 1,217 unmatched original instructions, top hunks at orig 0x420 (+60), 0xd70 (+57), 0x1728/0x1798, 0x4538.

## 5. On 1b0ae70 and after the landing (raw-IR capture + rx oracle; M first)

How the candidate was found (main 1b0ae70, M 2,125):

| trial | form | bytes | ratio | M |
| --- | --- | ---: | ---: | ---: |
| e1 | event `new_creator_fee_bps` read from the curve in the literal (`let nf` removed; the original reads +0x70 in the event, orig 0x4fd8) | 27,376 | 0.63689 | 2,125 |
| e2 | e1 + event `is_holder_reward` from the curve | 27,368 | 0.63429 | 2,116 |
| e3 / e4 | pool CPI `pargs.1 = holder` (hold) / + e1 | 27,424 / 27,400 | 0.63093 / 0.63331 | 2,107 / 2,114 |
| e5 / e6 | event `is_cashback_coin: cashback` / + pargs holder | 27,408 / 27,432 | 0.63322 / 0.62904 | 2,114 / 2,101 |
| f1 / f5 | curve stores holder before cashback (orig order), with / without e1 | 27,384 / 27,408 | 0.6332 / 0.63202 | 2,113 / 2,110 |
| f2 | e1 + `if let Some(f)=fee{curve.creator_fee_bps=f;}` (orig form) | 27,368 | 0.63729 | 2,126 |
| f3 | e1 + pool owner test first | 27,376 | 0.6351 | 2,119 |
| **g1** | event_authority clone, all fields via `a.pump_fees_event_authority` | 27,408 | 0.63801 | 2,130 |
| g3 | only key/owner/flags via `a.`, lamports and data via `x` | 27,376 | 0.6312 | 2,106 |
| g1e1 | g1 + e1 | 27,384 | 0.6392 | 2,133 |
| **g1 + ev_hr_curve** | landed | 27,400 | **0.6393** | **2,134** |
| g1 + cu_typed | | 27,352 | 0.62639 | 2,089 |
| g1e1 + g_w_clock_local / wl_ts_clockvar | +16 B fills | 27,400 | 0.63811 | 2,130 |
| g1e1 + ev_mint_key / ev_cb_local | | 27,400 / 27,392 | 0.63212 / 0.6379 | 2,110 / 2,129 |

Partial clone reloads on top of the candidate (the IR leads `%x19@exit191`, `%x.i@exit.i`, `%x11.i@exit199.i` on g1e1):

| trial | form | bytes | ratio | M (candidate 2,134) |
| --- | --- | ---: | ---: | ---: |
| k1 | sharing mint clone: owner, data via `a.mint` | 27,416 | 0.63642 | 2,125 |
| k2 | sweep TCF2 `program:` pump_amm clone: data via `a.pump_amm` | 27,416 | 0.63672 | 2,126 |
| k3 | sweep CpiContext pump_amm clone: data via `a.pump_amm` | 27,408 | 0.63801 | 2,130 |
| k4 | e1 on the candidate | 27,376 | 0.63719 | 2,126 |

On main 7e6aa9caa (0.6414, M 2,141; `irreM-7e6aa9c.tsv`), the re-read oracle has no clone x lead above main. The best clone
lead is `%x.i@exit.i` at M 2,137, +8 B. The only re-reads above main are holder_enabled `%33` (2,144 @ -40 B) and the
sharing pointer `%_370@bb1` (2,142 @ +8 B), which have no source form. The hold oracle on the candidate is below it
(best 2,131).

Zero-size knob screen on 7e6aa9c (22 catalog knobs from `sizeknobs-cto.json`, each applied alone): none beats main (M 2,141).
14 are byte-identical. cu_replace, g_old_fee_first and sh_fees_key give 2,140. g_canedit_first and g_s7_destrev give 2,139.
ev_ts_clockvar gives 2,131 and prep_match 2,128. e1 + wl_ts_clockvar / g_w_clock_local gives 2,130 @ 27,392.

On main d2d187555 (#3281, 0.6417, M 2,142) the re-read scan looks the same: holder_enabled `%33` 2,145 @ -40 B and the
sharing pointer `%_370@bb1` 2,143 @ +8 B, and no clone x lead at or above main. On the current main, the after-clobber
reload family is used up.

Fresh-path literals for `to_account_info()` on d2d1875: 14 unique sites (`X:a.F.to_account_info()` rewritten as
`AccountInfo{key:a.F.key,lamports:a.F.lamports.clone(),..}` in derive order). **All of them lose.** The best is
sharing_config, M 2,122 @ +16 B. The rest give M 1,118-2,097, often with a size jump of +400-650 B, because
to_account_info is an inlined library clone that sits in the same CPI account-list layout. Per site (M@bytes): sharing_config_sharing_config 2122@27416; quote_token_program_quote_token_program 1415@27808; pump_creator_vault_creator_vault 2032@27384; program_pump_fees 2097@27424; pool_authority_pool_authority 1657@27976; pool_pool 1681@27928; coin_creator_token_account_current_creator_quote_token_account 1202@28048; global_config_amm_global_config 1887@27800; authority_current_creator 1591@27928; authority_holder_creator_vault 1118@27920; associated_token_program_associated_token_program 2070@27400; authority_admin_set_creator_authority 2091@27368; associated_token_current_creator_quote_token_account 2084@27840; associated_token_holder_creator_vault_quote_token_account 1272@27864.
The mechanism only pays where the source already writes a hand-made literal with an `x` binding, and among those only
event_authority (#3267).

## Tools (experiment only)

| file | what |
| --- | --- |
| `tools/gaps.py` | largest unmatched hunks between the original and a candidate, by score tokens (imports w14a03 `irre_lib.py`) |
| `tools/rng.py <dis> lo hi` | print a hex offset range of a `sodis.py`/`dis.sh` listing |
| `tools/rec.py` | records a `res.jsonl` trial in the ledger |
| `edits/*.py` | the capvar EDITS lists above (b*/c* load `blib.py`/`clib.py` from this lane's out dir; copy them alongside) |
