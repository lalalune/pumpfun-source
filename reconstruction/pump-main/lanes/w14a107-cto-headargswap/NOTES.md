# w14a107-cto-headargswap: head/validate argument-vs-computed use-site provenance (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w14a82-cto-walletweight (#3409 landed holder-from-arg, notes #3432): its unimplemented next ideas
"other late-use-from-argument versus computed-value swaps in the head and validate" and idea 2 (what keeps the sweep-gate
flag out of r6-r8 once payload word 1 is in r9). The entry copy of `new` was left to pw9entry.
Bases: main 963d1ee (0.67226, M 2,244), 13fe453 (#3480, 0.67256, M 2,245), ebe5387 (#3495, 0.67316, M 2,247), all 3,123 slots.
Ledger: approach `headargswap`, keys `0x22a10-w14-{963d1ee,13fe453,ebe5387}-headargswap-*` (about 75 rows).

**Result: notes only, no gain.** 49 source spellings and 5 IR probes. Every form either folds to main's bytes or loses at
27,400 B. The best size-neutral composite is `fe_cs2_rp` (curve fee `match`, -8 B, plus the `rP_back` +8 B knob): 0.67286
against 0.67316 on ebe5387.

## Oracle

The w14a82 raw-IR capture (`capvar.sh` -> `capraw.py`, rustc `-C no-prepopulate-passes`) plus `rx.py` (`opt -O3` + llc),
re-pointed at this lane. The `base` capture reproduces each main (`eq_main: true`). One capture takes 20-55 s, and
`tools/batch.sh <list> <res>` runs two at a time (slots 0/1) and adds `M` (matched orig tokens, `wr.py`). The debug llc
(copied from w14a102) and `ra.sh` / `wtl.py` / `regmap.py` come from w14a82. `tools/rng.py <dis> lo hi` prints an
offset range of a disassembly, for side-by-side reading.

## 1. Per-use-site provenance after validate (original vs main 963d1ee/13fe453)

Entry argument spills. Original: `r3` holder -> `[r10-0x918]`, `r4` fee tag -> `[r10-0x928]`, fee value
`[r5-0x1000]` -> `[r10-0x930]`, new ptr `[r5-0xff8]` -> r7 (dies at the entry copy 0x4d8-0x538).
Main (963d1ee): holder -> `[r10-0x8e0]`, fee tag -> `[r10-0x910]`, fee value -> `[r10-0x930]`, new ptr -> `[r10-0x8e8]`, kept
until the sharing arm.

| use site | value | original source (offset) | main source | same? |
| --- | --- | --- | --- | --- |
| curve store 0xa5 `is_holder_reward` | holder | computed bool, i8 phi of constants, slot `[r10-0x950]` (0x4b60), no mask | holder **argument** reloaded `& 1` (from `[r10-0x8e8]` on 13fe453, a recoloured slot) | no; the arg form is #3409's +0.0048 |
| curve store 0xa3 `is_cashback_coin` | cashback | computed i1 phi `[r10-0x958]` `& 1` (0x4aa8), set at validate line 314 (orig +0xd78) | `and` of two head phis (`!holder`, `cashback byte!=0`), sunk to the store by MachineSink | no (w14a29 map) |
| curve store order | | 0xa5 before 0xa3 | same since #3480 | yes |
| curve fee tag test | fee tag | validate phi of constants (r7 = 1 on the fee-Some exit, 0 on None), slot `[r10-0x8e8]`, `jne r1,0,+1; ja +3` (0x4b80) | fee-tag **argument** spill `[r10-0x910]`, `jeq r1,1,+1; ja +3` | no (w14a54: the phi forms lose 0.08) |
| curve fee value | fee value | argument spill `[r10-0x930]` (0x4ba0) | same slot (0x4b58) | yes |
| old_fee | | curve `+0x70` read, spilled `[r10-0x8e0]` (0x4b50) | curve read, spilled `[r10-0x8f8]` | source yes, slot no |
| pool CPI tag (`[r10-0x1000]`) | fee tag | validate phi `[r10-0x8e8]` (0x4dc8) | argument spill `[r10-0x910]` (0x4d90) | no |
| pool CPI value (`[r10-0xff8]`) | fee value | argument spill `[r10-0x930]` | same | yes |
| pool CPI `r4` (is_holder_reward) | holder | computed phi `[r10-0x950]` (0x4e20) | curve re-read `[+0xa5]` into r8 (pargs.1) | no (`ph` forms cost +24..+32 B) |
| pool CPI creator | target | target pieces `[r10-0x580..0x568]` | same | yes |
| event `is_holder_reward` | holder | curve re-read `[+0xa5]` (0x4fe0) | curve re-read since #3480 | yes |
| event `is_cashback_coin` | cashback | curve re-read `[+0xa3]` | same | yes |
| event `new_creator_fee_bps` | nf | curve re-read `[+0x70]` at the event (0x4fd8) | `nf` local in r9 (#3437) | no (the #3437 RA gain) |
| event `old_creator_fee_bps` | old_fee | `[r10-0x8e0]` | `[r10-0x8f8]` | slot only |
| sweep PDA seed | holder_key | holder_key copy `[r10-0x518]` | holder_key copy | yes (`hk.0` forms below) |
| sharing arm `Some(args.0)` | new | new's entry copy pieces (0x655/0x658/0x900/r9/0x660/0x668) | new ptr `%391` plus tag byte `%15` and payload ptr `%16` kept live in registers from entry to the arm | no (pw9entry's residual) |

So the original reads **computed** values at the curve store and the pool CPI (holder `0x950`, cashback `0x958`, fee
tag `0x8e8`), and arguments only for the fee value. Main reads arguments, or the curve, everywhere. The only computed
reads that score well today are the ones the event takes from the curve.

## 2. Screens (raw-IR oracle; ratio / bytes / M)

On 963d1ee (main 0.67226 / M 2,244): `res1`. On 13fe453 (main 0.67256 / 2,245): `res2`-`res4`. On ebe5387 (main 0.67316 / 2,247):
`res5`, `res6`. Exact edits are in `edits/src/<name>.py`.

| family | spellings | best |
| --- | --- | --- |
| holder_key: `&hk.0` at validate / sweep / both, `let holder_key=hk.0`, `let (holder_key,_)=..`, `..find_program_address(..).0`, `&hk.0` reference | hk_val, hk_sw, hk_both, hk_let, hk_des, hk_dot0, hk_ref | hk_val folds to main tokens; hk_sw / hk_let -1 M (0.67286 on ebe5387); destructure/`.0` 0.559, reference 0.574 |
| new: `Some(new)`, `Some(Some(target))` in the sharing arm, validate takes `args.0`, `args` after validate | nw_su, nw_sut, nw_val, args_late | 0.43-0.53: every move of new's reads re-lays the frame |
| holder in validate/execute tests: computed `!holder` at 289, arg `hopt==Some(true)` at 296/298/314/execute cashback/shared tree, `unwrap_or` forms, `matches!`/`if let` for execute's holder | v289h, v289n, v296a, v298a, v314a, v314u, x_cba, x_tra, x_tru, h_mat, h_iflet, v298nw | `==Some(true)` swaps fold (GVN); v289h 0.66896 (3,121 slots, -14 M); `matches!`/`if let` for execute's holder are a different IR (-248 B, 0.598); 296/298 arg forms -440 B (0.426) |
| holder at the curve store / pool CPI: `matches!`, the tuple's computed bool (`_holder`, the original's provenance), pargs.1 from the arg | cs_hm, cs_hb, pa_hb, pa_hopt | cs_hm folds; cs_hb 0.66018 @27,408; pa_hb 0.63054 @27,432 |
| cashback at the event from the computed local | ev_cb | 0.66577 @27,392 |
| fee tag at the curve store: `match` Some-first / None-first, `!=None`, `!is_none()`, `map_or`, `if let ..=&fee` | fe_cs, fe_cs2, fc_none1, fc_ne, fc_isnone, fc_map, fc_ifletref | `is_some`/`!is_none`/`&fee` fold; the `match`/`!=None` forms are one `-8 B` single `jeq r1,0,+3` (the anti-original form; the original keeps the pair) at -6 M |
| fee at the pool CPI: `fee.map(\|_\|nf)`, `if fee.is_some(){Some(nf)}`, `fee.and(Some(nf))`, `fee.map(\|f\|f)` | fe_pa, nf_pa, pa_fflt, pa_fcopy | identity map folds; nf forms -8 B / -8 M |
| target at the pool CPI from the curve | pa_tgt | 0.54562 @27,568 |
| old_fee moved copy at the event | of_ev | folds |
| sharing key: one `sk` for the shared test and validate (`sk0`, hoisted `sk`), `a.sharing_config.key` reference, inline `&..key()` | sk_one, sk_one2, sk_ref, sk_key | 0.54-0.62: #3495's duplicate `key()` calls are load-bearing |
| -8 B pairs with +8 B knobs (`we` `is_writable==false`, `cn` `collection_native==false`, `rp` rP_back) | fe_cs2 / fe_pa x we / cn / rp | fe_cs2_rp 0.67286 (M 2,246); fe_cs2_we 0.67256 with 3,094 slots (-29), fe_pa_we 3,093 slots; none above main's ratio |

IR probes (post-opt `rx/base/m.ll`, `tools/run.sh`):

| probe | ratio / bytes / M |
| --- | --- |
| ihr / ihr1: holder byte recomputed at the 0xa5 store as `(h&-3)!=0` / `h==1` (w14a82's `hr` lead) | 0.66627 @27,424 / 2,225 (the lead is gone after #3480) |
| ihre: `xor` of the entry compare | 0.65948 @27,416 |

## 3. Idea 2: with payload word 1 in r9, why the sweep-gate flag is not spilled (13fe453)

`q9` / `q8`: an empty `asm sideeffect "", "{r9}"` / `"{r8}"` use of `%_0.sroa.11.1` before `%770 = insertvalue` (oracle only).

| oracle | ratio | bytes | M | F / Fw | wallet reg diffs | regmap top |
| --- | ---: | ---: | ---: | --- | ---: | --- |
| main | 0.67256 | 27,400 | 2,245 | 0.75614 / 409 | 54 | r9->r7 30, r9->r8 21 |
| q8 (control) | 0.60855 | 27,312 | 2,028 | 0.72078 / 406 | 54 | r8->r9 40, r9->r8 39 |
| q9 | 0.62397 | 27,328 | 2,080 | 0.73796 / 426 | 30 | r9->r8 gone |

The pw9 lead holds on 13fe453 (+52 M over its control, same as w14a82 measured on 0d04cf4).

The flag `%60` ([18000,33536), w 4.62e-06) in q9 (`results/tl_q9_flag_new.txt`):
- At step 326 it takes r6 and evicts the sharing tag `%59`.
- At step 457, new's tag byte `%15` (`LDB %391,0`, [3504,19760), w 3.25e-04) evicts it. That byte is read by the sharing arm's
  `Some(args.0)`, and new's payload pointer `%16` ([3728,19504)) takes r9 next to it.
- It then takes the free r8 at step 459, under q8 the free r9.
- At steps 1782-1786 a `%1575` piece (the cashback `!holder` phi) evicts it again, and it splits into r8 pieces. It is never spilled.

So once word 1 holds r9, nothing heavier than 4.6e-06 occupies r8 over bb26-bb35. In the original the flag is spilled at
its def, so r6-r9 must carry heavier values there. The values main keeps live across that range and the original does
not are new's tag byte and payload pointer (`%15` / `%16`, which the original's entry copy replaces with stack pieces) and the
cashback operand phis (`%466` / `%467`, a single computed `[r10-0x958]` in the original). Both are blocked: the entry copy
belongs to pw9entry (#3384, w14a96/w14a102), and cashback provenance is w14a29's dead end (every 9-crossing spelling loses
0.05-0.18). An entry-copy spelling should be checked for both: `regmap` `r9->r8` dropping, and `wtl.py ra.log 17000 34000 %60`
showing no free r6-r8 after step ~457.

## 4. Next ideas

- The provenance table says the original's curve store and pool CPI read three **computed** values (holder 0x950,
  cashback 0x958, fee tag 0x8e8). Main reads arguments for all three. Each computed form alone loses through RA or frame
  cascades (cs_hb -0.012, ph -0.026, fee-tag phi -0.08). They are only worth retrying together, on a skeleton
  where the entry copy of new already frees `%15` / `%16` (pw9entry), so the head pressure matches the original's.
- `fe_cs2_we` / `fe_pa_we` cut slots to 3,093-3,094 (-29) at 27,400 B while ratio drops 0.0006-0.0012. That is a frame-position
  lever, not a ratio one, if the ranking ever changes.

## Files

`edits/src/*.py` (source EDITS for `capvar.sh`), `edits/ir/*.py` (post-opt IR EDITS for `pe.sh`/`run.sh`), `results/res1-6.txt`
(oracle rows), `results/tl_q{8,9}_flag_new.txt` (greedy timelines of `%60`, `%15`, `%16`), `tools/batch.sh`, `tools/rng.py`.
