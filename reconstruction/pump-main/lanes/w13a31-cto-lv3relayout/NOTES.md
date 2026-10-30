# w13a31-cto-lv3relayout: why lv3 relays out, and the source form that keeps the original layout

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
This lane continues w13a18-cto-feephi (#2979). lv3 (`trials/lv3.py`) gives the original's three fee-None threads, and
its errseq equals the original except for 306. But it measures 0.26 plain and 0.561 frame-masked, against main's 0.686.

All numbers come from the raw-IR opt oracle: w13a01 `rx.py`, run through `capvar.sh` and `runq.sh` from w13a18.
fm is the frame-masked ratio and sk the skeleton ratio (frame offsets and registers masked), both from w13a18 `absratio.py`.

## 1. Where lv3 loses: one block-chunk swap

`tools/callperm.py orig.ann cand.ann` aligns the call/exit landmark sequences and prints matched runs with their shift.
`tools/annobj.py` writes the `annot.py`-style listing for an llc object, with call labels taken from relocations.

On main 6ac6f9b, lv3 swaps two large chunks:

| orig range | content | lv3 position |
| --- | --- | --- |
| 0x3c40-0x4a78 (463 insns, no calls) + 0x4a78-0x5510 | post-sweep join, curve/state stores, sharing-config CPI | +0xda8 (after the chunk below) |
| 0x55d8-0x6320 | error tail, `exit`, native sweep (Rent / ensure_rent_exempt / transfer_native), token sweep (token_frozen, create_idempotent, transfer_vault_tokens), collect | -0x1950 (directly after the Rent::get Err `::from`) |

Per-0x800 region coverage (`regcov.py`, frame-masked) shows the cost: orig 0x5000 0.89 -> 0.42, 0x5800 0.74 -> 0.00, 0x6000 0.87 -> 0.60.
Other regions are about equal to main, and lv3 is better at 0x1000 (0.59 -> 0.70).

## 2. Mechanism: a MachineBlockPlacement fallthrough veto at the sweep-exit join (not BFI drift)

IR block frequencies are scaled uniformly (x0.907) between main and lv3 inside the sweep, and the post-opt CFG there is identical.
The difference is in `llc` (`-stop-after=block-placement` MIR, `mirp_*.mir`):

- The sweep-exit join (`bb58.i`/`sweep.exit`, `jne rX,2`) is entered from the Rent::get Err `::from` block (`bb82.i`, the
  candidate fallthrough). It is also entered from a phi-copy block (`$r7 = MOV r1`) that collects the token/native-sweep Err
  edges: `bb86.i` (ensure_rent_exempt), `bb103.i` (create_idempotent) and, in lv3 only, `bb105.i` (transfer_vault_tokens).
  In main, `bb105.i` already has the tag in the join register and goes to the join directly.
- `hasBetterLayoutPredecessor` vetoes the fallthrough when an unplaced predecessor's edge frequency is at least 0.25x the
  candidate's (HotProb 80%). Main: copy block 3.33e-5 vs 0.25 x 1.46e-4 = 3.66e-5, so the fallthrough is kept.
  lv3: 3.55e-5 vs 0.25 x 1.33e-4 = 3.32e-5, so it is vetoed (ratio 0.267 against 0.25).
- With the join vetoed, the chain continues from the worklist into the error/exit/sweep chunk, and the join plus the
  post-sweep code are placed after it. That is the swap in section 1.

IR proof (`tools/bwfm.py run <lv3 m.ll> SPEC`): `bw:bb104.i:20:1` makes the transfer_vault_tokens Err edge rarer. It
restores the original order at the same 27,336 B: fm 0.561 -> 0.662, sk 0.650 -> 0.867. Main's sk is 0.853.
The w13a26-style sweep (`bwfm.py sweep`) shows that `inv` on the native test (bb25.i), the amount==0 test (bb44.i) or the
Rent Ok test (bb26.i) also fixes it, as do several validate-region weights. The margin is about 7%.

## 3. Source forms that keep the layout (lv3 family)

| trial (main 6ac6f9b) | change on top of lv3 | bytes | ratio | fm | sk | fee tests | errseq |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| main | | 27,400 | 0.56291 | 0.68604 | 0.85321 | 2 | 298 289 296 326 306 312 307 330 338 410 334 .. |
| lv3 | (w13a18) | 27,336 | 0.26365 | 0.56149 | 0.64997 | 3 | 289 298 296 326 306 312 307 330 338 334 410 .. |
| **s_map** | token arm written like the native arm: `if frozen{require!(..);Ok(amount)}else if amount>0{create_idempotent(..)?;transfer_vault_tokens(..).map(\|()\|amount)}else{Ok(amount)}` (the line-720 `Ok(amount)}` becomes `}`) | 27,320 | 0.31833 | 0.66187 | **0.86679** | 3 | = lv3 |
| s_rentlet | `let rent=Rent::get()?;let min=rent.minimum_balance(0);` | 27,344 | 0.31819 | 0.66097 | 0.86520 | 3 | = lv3 |
| s_andthen_nat | `ensure_rent_exempt(..).and_then(\|()\|transfer_native(..)).map(..)` | 27,312 | 0.32258 | 0.66017 | 0.86722 | 3 | = lv3 |
| v306e | s_map + `let t=new.ok_or_else(\|\|error!(..CtoNewCreatorRequired))?;` | 27,416 | 0.26505 | 0.68044 | 0.84546 | 3 | 298 289 .. |
| s_rentmap / s_natamt0 / s_tokelse | `Rent::get().map(..)?` / `else{Ok(0)}` / `amount!=0` | | = lv3 | | | | |
| v306a-d | let-else, None-first match, `if let Some(_)`, `is_none()` polarity on 298/306 | | = s_map (byte-identical) | | | | |

s_map is the natural spelling, because the native arm already ends in `.map(|()|amount)`. It holds the original block
order with all three fee-None threads. Its skeleton is above main's, so lv3+s_map has the better structure. What still
separates it from main:

- **Frame.** `tools/fdelta.py` maps aligned frame references orig -> cand. In main the 0x28-0x450 band is exact (903 of
  1,230 aligned refs). In s_map that band is +0x10 and only 160 of 1,228 refs are exact. A 16 B pair (`stdw [r10-0x10],1;
  stdw [r10-0x18],0`; orig -0x28/-0x30) moves to the top of the frame, and the 32 B-allocas push the rest down. The frame
  top is 0xc50 against orig 0xc38 and main 0xc30.
- **Registers.** fm is 0.662 against main's 0.686 although sk is higher, so lv3's live ranges change register choice.
- **306.** No local spelling of the 298/306 sites moves 306 (v306a-d are byte-identical).

## 4. On main cc475bf (0.59197): the s_map gene alone

| trial | bytes | ratio | slots | fm | sk |
| --- | ---: | ---: | ---: | ---: | ---: |
| main cc475bf | 27,400 | 0.59197 | 3,311 | 0.68814 | 0.84871 |
| m_map (s_map edits only) | 27,376 | 0.59254 | | 0.68785 | 0.84819 |
| m_map + rentlet | 27,400 | 0.59107 | 3,264 | 0.68634 | 0.84572 |
| lv3 | 27,360 | 0.20717 | | 0.55674 | 0.65537 |
| lv3 + s_map | 27,344 | 0.26121 | | 0.65707 | 0.86280 |

m_map is +0.00057 at -24 B. A screen of the 15 `sizeknobs-cto.json` knobs that still apply found no companion at
27,400 B that stays above main. The best at 27,400 is `s_rent_local`, which is the same as m_map + rentlet. The gene is
also not faithful: the original keeps a separate transfer_vault_tokens Err edge (orig 0x60c0: `ldxdw r7,[..]; jeq r7,2;
ja +0x5a`), with the tag loaded straight into the join register r7. So the original holds the layout through register
allocation, not through the `.map` form. In lv3 the join phi gets r6 (`jeq r6,2` after transfer_creator_fees_to_pump_v2),
which forces the r1->r6 copy block and the veto. **The faithful fix is RA: the sweep-exit tag in r7, as in main and the original.**

## 5. More lv3 screens on main cc475bf (raw-IR oracle)

| trial | change | bytes | ratio | fm | sk | note |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| L1 / L4 / L10 / L11 | hb,shared params last; `target=st.creator` init; `let _=validate(..)?`; `Ok(*sharing)` | 27,360 | 0.20717 | 0.557 | 0.655 | byte-identical to lv3 |
| L3 / L3m | `target=Pubkey::default()` init (without / with s_map) | 27,512 / 27,496 | 0.21016 / 0.26077 | 0.558 / 0.653 | 0.642 / 0.849 | |
| L9 / L9m | holder_key PDA before `shared` (original 0x140 order) | 27,448 / 27,432 | 0.25232 / 0.2521 | 0.514 | 0.651 | new swap: sweep chunk orig 0x24d0-0x3bd0 placed after the sharing CPI, even with s_map |

lv3 sits near several MBP thresholds. s_map fixes the sweep-exit one, and moving the PDA first trips another.

**306.** A bw 1:2000 / 2000:1 / inv sweep over all 150 branches of lv3+s_map (`sw_smap.jsonl`, 450 runs) never gives the
original errseq. 413 runs keep lv3's order. bb97.i 1:2000 gives `289 298 296 306 312 307 330 338 334` (326 lost). So
306-after-298 is not a single-edge frequency effect on this CFG.

**Frame oracle** (`frsweep.py` on lv3+s_map, 141 allocas x {mv FIRST, mv END, nolt}): the best single edit is
`nolt:t.i` (validate's `t`), 0.26121 -> 0.34908. Next are `nolt:sk` 0.336 and `nolt:target` 0.333. Greedy accumulation
(`frgreedy.py`) stops after one step. IR-level slot order and coloring cannot bring the lv3 family near main's 0.592. Its
frame needs a different set of allocas (the 32 B `target` / creator copies), not a reordering.

## Conclusion

The lv3 relayout is fully explained: an MBP fallthrough veto at the sweep-exit join, at a ratio of 0.267 against the 0.25
limit, caused by one extra phi-copy edge that comes from register allocation. The token-arm `.map` spelling restores the
layout in source, and lv3+s_map's skeleton is above main's (0.867 against 0.853 on 6ac6f9b; 0.863 against 0.849 on
cc475bf). Plain ratio (0.26-0.32) and fm (0.657-0.662) stay below main because of the frame (the 0x28-0x450 band at +0x10)
and register choice. The original errseq (306 after 298) was not reached. The angle is exhausted as a landing route at
this size; the residuals are frame/RA.


## Tools (`tools/`; experiment only)

- `annobj.py <m.o>`: annot.py-style listing of an llc object, with call labels from relocations.
- `callperm.py orig.ann cand.ann`: chunk permutation map (greedy longest common call-landmark runs, with shifts).
- `bwfm.py run|sweep <m.ll> ...`: w13a26 `bwx.py` with plain + frame-masked + skeleton scoring.
- `frsweep.py run|sweep <m.ll>`: alloca-level frame oracle (`mv:A:FIRST|END|B`, `nolt:A`, `sz:A:N`, plus bw/inv).
- `fdelta.py <m.dis>`: orig -> cand frame-offset map over frame-masked aligned instructions.
- `chunkshow.py label occ ann..`: print the n-th chunk ending in a given call from several listings.

Ledger keys: `0x22a10-w13-6ac6f9b-lv3relayout-*`, `0x22a10-w13-cc475bf-lv3relayout-*`.
