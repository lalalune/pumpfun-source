# w14a34-cto-curvetail: the curve update after the sharing CPI, and its effect on the pool CPI

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 5ee681d (0.645), 81d3d9a (0.65069), faf9962 (0.65129, M 2,173) and 6db95a7 (0.65458, M 2,184). Each row was
measured on the main it is reported against.
Ledger: approach `curvetail`, keys `0x22a10-w14-{5ee681d,81d3d9a,faf9962,6db95a7}-curvetail-<name>-v1` (about 270 rows).

**Result: no zero-loss gain. The curve tail is a mapped dead end.** About 170 distinct source forms were tried
(store order, read position, curve-reference derivation, fee and flag spellings, pool gate, pool args, event fields,
sharing-arm match forms). None beats main at 27,400 B. The best results either equal main's tokens or sit 1 M below it.

## Oracle

The oracle is the raw-IR capture plus `opt -O3` and `llc` (`tools/capvar.sh`, `tools/rx.py`, `tools/capraw.py`,
repointed from w14a30). `m0` reproduces a fresh `measure.sh` build of main byte for byte (5ee681d, faf9962).
- On 5ee681d the published baseline `unstripped.so` differed from a fresh build of the same MAIN_SHA in the sharing CPI
  (0x41e8-0x42b8, 59 tokens) at the same ratio. Compare against your own `m0` capture, not `eq_main`.
- `e/runboth.sh <list> <res>` runs a two-worker queue (`e/runq.sh`).
- `e/comb.py` concatenates edit lists. `e/gen*.py` generate the screens. `e/rec.py` writes the ledger rows.
- `tools/llcrun.py` applies post-opt IR edits and runs llc only.
- M is the number of matched score tokens, which is ratio × (3,337 + candidate tokens) / 2.

## 1. The original's curve update against ours (orig 0x4a78-0x4c58, main 0x49f8-0x4c18)

| | original | main |
| --- | --- | --- |
| CPI-return branch | `jne r7,2,+0x147` (one insn) | `jeq r7,2,+1; ja +0x1c1`: jump-around, +8 B (BPF cannot reverse branches; the join bb38 precedes the CPI in IR order) |
| hoisted before the branch | `r6=[0x8f8]` sharing tag (kept to the event, split around the pool run), `r2=[0x950]` holder phi slot | none |
| curve base register | `r3=[0x8d8]`, a scratch-register reload of the accounts spill slot | `r6=[0x8e0]`, kept live through the pool gate and the pool clone run |
| store order | creator, **holder 0xa5** (phi slot 0x950, stored as is), **cashback 0xa3** (phi slot 0x958 `&1`), fee if-let ([0x8e8] tag, [0x930]), can_edit 0xa4 | creator, cashback (`[0x8f8]&[0x908]&1`: sunk `curve_cb & !holder`), holder (`[0x8d8]&0xff != 0` select into r9, kept for the event), fee, can_edit |
| reloads of the curve Box ptr `[base+0x38]` | before every store (5) | before every store (5): same |
| nf after the stores | none (the event reads +0x70 at orig 0x4fd8) | `ldxdw [r6+0x38]; ldxdw +0x70; stxdw [0x8d8]` |
| pool gate | owner memcmp first, with the pool ptr in r7 across the memcmp, then `data_is_empty(r7)` | `data_is_empty([r6+0x70])` first, then a reload and the memcmp, so the accounts pointer stays live across both calls |
| pool run head | `ldxdw r6,[0x8d8]` (accounts reload), holder arg `ldxdw r4,[0x950]` | `ldxdw r1,[r6+0x38]; ldxb r8,[r1+0xa5]` (pargs.1 from the curve), `mov r4,r8` |

- The original's holder and cashback are phi slots. Validate's arms write them (orig 0x0db8/0x0e40, 0x1130/0x1138, 0x14e0, 0x1830/0x1850, 0x18b0/0x18b8).
- Ours are entry-block i1 values that ISel and MachineSink sink into the store block, so they are recomputed there.
- Store order alone cannot fix this. Every holder-first order costs 8 B and 0.004-0.008, because holder stays an
  icmp+select, not a slot.

## 2. Screens

Ratios are at 27,400 B unless a size is given. Each base main is listed in the header.

| family (base) | forms | best | result |
| --- | --- | --- | --- |
| store order (5ee681d): all 24 orders of cashback/holder/fee/can_edit after the creator store, plus 8 with the creator later | p_* | TCHEF / TCEHF / TECHF 0.6447 (main 0.645) | holder-first orders 0.6398-0.6401 @27,408; creator-later 0.6374-0.6392 |
| old_creator/old_fee read position, `mem::replace` (5ee681d) | r_* (7) | r_of_first, r_oc_replace 0.6438 | loss |
| curve reference derivation (5ee681d): `&mut *`, `&mut **`, typed `&mut BondingCurve`, `as_mut()`, repeated `ctx.accounts.bonding_curve.` paths | d_* | `d_paths` = main tokens; deref forms 0.63289 @27,360 (-40 B: data pointer loaded once) | loss / identical |
| fee spelling (5ee681d): match, is_some+unwrap, unwrap_or(old/cur), map, as_ref, `let p=&mut` | f_* (7) | f_issome, f_ifletmut = main | identical / loss |
| flag spelling (5ee681d): tuple assignments, `if holder{true}else{false}`, branchy per-arm stores | h_* (6) | tuple and ifset forms = main | branchy 0.549 |
| pool gate / pargs / nf / event (5ee681d): own (owner-first, the original form), ph (pargs.1 holder), hf, e1 (event nf from curve, no `let nf`), evhr, evcb, nf/pargs position. Full factorial over 6 toggles | g_* (70) | g_nf_blk = main; g_e1 0.64499 @27,376 (-1 M) | all below main |
| sharing-arm `if let` (s_iflet, -8 B) × curve variants (81d3d9a / faf9962) | si_* (19) | si_g_e1 0.65138 @27,368 (-1 M), si_f_unwrapor_cur 0.65099 @27,400 (-1 M) | below main |
| sharing-arm match spellings, alone and with e1 (faf9962) | m_* (16) | m_nonefirst / m_match_unit = main | by-ref forms 0.545 |
| on 6db95a7, after w14a33 landed e1 as its size repay: s_iflet plus +8 B tail partners (nf restored before or after the gate, from the curve block or as an event-local; event fee `fee.unwrap_or(old_fee)`; evcb; evhr; store orders; owner-first gate; ph) | v_* (28) | `nf` as an event-local = main; s_iflet alone 0.65438 @27,392 (-1 M); si_f_unwrapor_cur 0.65428 @27,400 (-1 M) | below main |
| w14a21 validate-closure leads (vy1, vy1n, v7c, vx1, vy2, vy3, v7c2n) repaid with tail knobs (faf9962) | y_* (49) | vy1 + si + e1 0.6476 @27,408 (M 2,161 vs 2,173) | the closures are -12 M raw on faf9962; no tail knob repays that |

## 3. Mechanisms other lanes can use

- **The accounts pointer across the pool gate comes from the gate order, not from the curve stores.** With the
  owner-first gate (`a.pool.owner==&AMM && !a.pool.data_is_empty()`) the pool pointer is loaded once and held in a
  callee-saved register across the memcmp, as in the original (memcmp is argmemonly, so GVN keeps the load).
  - With e1 as well, the gate skeleton equals the original's (ch3 +3/+4 sk in 0x4800).
  - Raw still loses 4-6 tokens: the pool pointer is r6 (orig r7), pool_updated r6 (orig r8), and the accounts pointer
    stays live in r8 into the pool run because pargs.1 and the clones need it. The original spills it.
  - This is the w14a01/w14a12 callee-saved occupancy problem. The original's r6/r7/r8/r9 hold the tag, the pool ptr,
    pool_updated and swept.
- **The `if let` sharing arm gives the original's single `jne r7,2` at the sharing CPI return** (main has `jeq;ja`).
  - It is +1 under jump masking (+3 with e1).
  - It is -5 M raw because it removes 8 B from orig 0x4400-0x4c00, which is already about 128 B short of the original
    (w14a31 profile), so every jump that crosses it gets further from the original's distance.
  - A landable form needs a faithful +8 B in the same region (the sharing CPI clone run, 0x4000-0x4a80) to go with it.
- **e1 (event `new_creator_fee_bps:a.bonding_curve.creator_fee_bps`, no `let nf`) plus s_iflet is the cheapest
  size knob found: -32 B for -1 M** (faf9962). e1 alone is -24 B for -1 M. s_iflet's -5 M disappears when e1 is
  combined with it.
  - w14a33 (#3315, 6db95a7) has since landed e1 as the size repay for its native-arm join.
  - On 6db95a7, s_iflet alone is -8 B for only -1 M (0.65438 @27,392). It is the cheapest -8 B knob for pairing with
    a +8 B lead.
- A post-opt IR probe that puts holder and cashback in memory (allocas stored at their definitions and loaded at the
  stores) re-colours the whole function (M 2,172 -> 1,609, even with the frame remapped). The phi-slot representation
  is a whole-function RA property, as w13a38/w13a51 found.

## 4. Dead ends (do not repeat)

- Curve store order in any permutation; holder-first is always +8 B and a loss.
- Curve reference derivations: `&mut *`, `&mut **`, typed, `as_mut`, repeated paths, an accounts let.
- Reading old_creator/old_fee later, or with `mem::replace`.
- Fee and flag spellings, including tuple stores and branchy per-arm stores.
- Pool gate owner-first alone or with ph/hf/e1/evhr/evcb, and every combination of the six toggles.
- The nf position, a block-returned nf, and pargs bound first.
- Sharing match forms: None-first, `if let`/else, by-reference (`&sharing_update`), `.as_ref().copied()`, wildcard, unit.
- Tail knobs as size repay for the vy1/v7c validate closures.

## 5. Next ideas

1. Pair s_iflet (-8 B, the original CPI-return branch) with a faithful +8 B inside the sharing CPI clone run, where
   ours is about 128 B short of the original. The w14a30 literal-order lane works in that region.
2. Make holder and cashback phi slots from validate's arms without the h2 cascade. That means the swept/tag
   callee-saved occupancy (w14a01 section 3) has to move at the same time. It is not a curve-tail lever.
