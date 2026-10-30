# w14a09-cto-pdara: holder_key PDA first + register-assignment partners (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: w14a02-cto-validatecr (#3209) next idea 1. `pda` (holder_key PDA before `shared`, the original's call order at
orig 0x98-0xf8) is the only validate-region step that clears the skeleton bar, but it loses on register assignment in
orig 0x3000-0x3800. This lane looks for a source partner that keeps main's tail RA while the PDA call moves first.
Bases: main 769f331 (0.63241) for the screen; main cef0574 (#3210, 0.63421) for the re-checks; main b174038 (#3250, 0.63571) final check: pda 0.56573, pda+hL 0.56663 (27,360 B), the same payload r6 / split r6 cascade (`results5.jsonl`).
Scratch: `~/.cache/pumpfun-reconstruction/lanes/w14a09-cto-pdara/` (not in git).
Ledger: approach `pda-first-ra-partner`, keys `0x22a10-w14-{769f331,cef0574}-pdara-*`.

**Result: no zero-loss gain, no source change.** The pda front is worth at most +0.005 even with a perfect partner
(splice bound below), and no partner in 285 source screens (263 single partners on 769f331, 22 on cef0574) keeps main's tail RA. Best pda composite:
pda+hL+g_ev_reset_shared 0.57426 at 27,208 B on 769f331 (main 0.63241); plain pda+hL 0.56548 on cef0574 (main 0.63421).

## Oracles

All numbers come from the raw-IR capture + `opt -O3` + extracted `llc` oracle (w14a02 `capvar.sh` + `rx.py`). It
reproduces both mains exactly (769f331 0.63241 `eq_main`; cef0574 0.63421).

- `tools/pscreen.sh` / `pscreen2.sh <slot> <list>`: source partner screen. Each line names genes joined by `+`, applied
  after `pda` (`e/g2.py`: hand genes `h*`, plus every w13a47 `genes47` gene (`g_*`) and every `sizeknobs-cto.json` knob
  (`k_*`) that applies to the pda source (`e/applic.py`, 253 of 371)). Each row is ratio, bytes, rm/fm chunks, and coal.py
  (payload class register, `%0` split register, clonefeat).
- `tools/exsum.py`: exact-match instructions per 0x800 orig region (global alignment), so the tail loss (0x3000/0x3800)
  is visible at a glance.
- `tools/pe2.py <m.ll> <name> <edits.py>`: post-opt IR edit -> llc -> ratio, rm, coal (no build slot, ~10 s).
- `tools/splice.py <front.o> <back.o> addr..`: bound. It splices front's instructions up to an orig address with back's
  instructions after it, then scores the result with the score.py-equivalent masked metric.
- `tools/ovl.py <ra.log> <vreg> <reg>`: which already-assigned vregs on a register overlap a vreg's segments at the
  moment greedy RA selects it (why the payload class cannot take r8). `occ.py`, `r8at.py`, `pairs.py`: register
  occupancy and register-pair census helpers.

## What pda changes (769f331)

Exact-match instructions per 0x800 orig region (`exsum.py`):

| | 0x0 | 0x800 | 0x1000 | 0x1800 | 0x2000 | 0x2800 | 0x3000 | 0x3800 | 0x4000 | rest | total | ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| main 769f331 | 76 | 85 | 68 | 142 | 167 | 152 | **161** | **170** | 90 | 715 | 1826 | 0.63241 |
| pda | 90 | 83 | 68 | 137 | 160 | 133 | 30 | 107 | 88 | 698 | 1594 | 0.56338 |
| pda + hL | **93** | 83 | 68 | 137 | 160 | 133 | 30 | 107 | 88 | 698 | 1597 | 0.56428 |

- **hL** (`shared` tests `a.bonding_curve.creator==a.sharing_config.key()`) is the original's operand order when the
  PDA comes first. The curve pointer is loaded before the sharing pointer (orig 0x140/0x148) and passed as memcmp r1.
  It is +0.0009 over plain pda and is the base for the screen. On main, without pda, stitch9's key-left form is right.
- The front gain is only **+17 exact** instructions (orig 0x0-0x800). The +35 rm of w14a02 are mostly register and frame
  differences that stay different (the entry RA is r6=accounts, r9=args, r7=curve; the original has r8=accounts,
  r6=args, r9=curve, r7=`new` pointer, with the sharing pointer spilled to -0x8e0).
- The tail loss is **-194 exact** in orig 0x3000-0x3800 (fm 193 -> 51). It is a register shuffle in the AccountInfo
  clone runs, and the frame shifts by 8 there (one extra spill slot).

## Mechanism (debug llc, `-debug-only=regalloc`)

1. Main computes `shared` before the PDA. Its global-pointer load (`%5`, accounts+8) occupies r8 over the entry
   (1792r-3040r), so `cashback` (`%471`, live from validate to the final `curve.is_cashback_coin` store) cannot take
   r8: it evicts and is evicted. The Err-payload class (`%1668`) then finds **r8 free** and takes it directly.
2. With the PDA first, r8 is free when `cashback` is allocated, so it takes r8 for its whole span (2096-64560). When the
   payload class is selected, r6, r7, r8 and r9 all overlap it (`ovl.py`). Greedy evicts `%62` from r6 and the class
   lands on **r6**. In turn the accounts-pointer `%0` region split costs more on r8 (static 3.0057 -> 3.1625, now worse
   than r6 at 3.1232) and moves to r6 in 88 bundles. The clone-run region then reshuffles.
3. The coupling is not just `%0`. IR oracle `pe/rl.py` reloads the sharing pointer (as the original does from -0x8e0).
   The `%0` split goes back to r8 (96 bundles), but orig 0x3000/0x3800 drop further (19/77 exact).
4. The payload class is not the whole story either. IR asm pins of the payload phi (`pe/payr{6,8,9}.py`) on both bases:

| pin | main 769f331 | pda + hL | gap |
| --- | ---: | ---: | ---: |
| none | 0.63241 | 0.56428 | -0.068 |
| r8 | 0.58945 | 0.58211 | -0.007 |
| r9 (original) | 0.58907 | 0.57983 | -0.009 |
| r6 | 0.60317 | 0.52056 | -0.083 |

   With the payload class held on the same register, pda is still 0.007-0.009 below main.

## Bound

`splice.py` scores pda+hL's own instructions up to orig X joined with main cef0574's instructions after X:
0.63891 (X=0x400), 0.6391 (0x800), 0.6391 (0x1000), 0.63929 (0x18a0), against main 0.63421. **The whole pda angle
is worth at most +0.005, and only if a partner leaves main's tail RA untouched.** Every partner measured so far
reshuffles the tail.

## Partner screen

pda+hL + each applicable genes47 (`g_*`) / sizeknobs (`k_*`) gene, 769f331 (main 0.63241): 263 rows, 216 compiled
(the 47 failures are k_/g_ duplicates whose pattern hL or another gene already consumed). Every row is below
main; 12 beat plain hL. Full rows: `results2.jsonl` (769f331) and `results3.jsonl` (cef0574).

| trial | bytes | ratio | exact 0x0 / 0x3000 / 0x3800 | tail exact (main 331) | payload / `%0` split |
| --- | ---: | ---: | --- | ---: | --- |
| hL+g_ev_reset_shared (= g_rs_presig = k_ev_reset_shared) | 27,208 | **0.57426** | 96 / 70 / 119 | 189 | r9 / r8 |
| hL+g_ev_cb_local (= g_ev_cbl, g_e_cb_local) | 27,384 | 0.56728 | 93 / 29 / 110 | 139 | r6 / r6 |
| hL+g_pre_cb_match / g_pre_cb_not | 27,384 | 0.56518 | | 137 | r6 / r6 |
| hL+g_v_cbv_fwd | 27,256 | 0.53560 | 93 / 74 / 136 | 210 (but 0x800/0x1000 fall to 41/27) | |
| hL+g_okp_hold | 27,368 | 0.55036 | | 186 | |

Round 2 on cef0574 (main 0.63421): hL+ev_reset_shared+ev_cb_local 0.57658; +okp_hold 0.56122; +v_cbv_fwd 0.56253
(tail 269, but validate falls); hL+okp_hold+v_cbv_fwd 0.51352. Without pda, g_ev_reset_shared alone is 0.58403.
The partners that move the tail toward main's tail all break another region, and none comes near main.

Hand partners (`e/g2.py`), all applied after pda:

| gene | form | ratio (769f331) | note |
| --- | --- | ---: | --- |
| hL | creator-left shared memcmp | 0.56428 | best hand partner, orig order |
| hBC | `let bc=&a.bonding_curve` before the PDA | = pda | GVN folds it |
| hIF | `shared` as `if key==creator{..}else{false}` | 0.5624 | |
| hK1 / hK2 | `let holder_key=FPA(..).0` / `let (holder_key,_)=FPA(..)` | 0.53701 | PDA result as a temp |
| hSK / hSKp | `sk=sharing_config.key()` bound before / after the PDA and used by `shared` | 0.53381 / 0.52863 | |
| hQL | quote_locked before shared | 0.54924 | payload r8, split r9, tail 186 exact |
| hMint | PDA seeds use `a.mint.key()` inline | 0.55775 | +80 B |

On cef0574 (0.63421): pda 0.56458, hL 0.56548, hL+hHold (holder bool bound at entry) 0.55314, hL+hCb (cashback byte
read at entry) 0.53633, hL+hHoldE (`matches!`) 0.54613, hL+hMay 0.47926. Partners on the final curve stores: hL+cbS (`curve.is_cashback_coin=curve.is_cashback_coin&&!holder`) / cbA (`&=!holder`) / cbIf (`if holder{..=false}`): 0.55278 / 0.55278 / 0.55298. They move the payload class to r8 and the split to r9, but the tail stays at 147 exact. hRs (holder recomputed from the argument at the store) is byte-identical (GVN folds it).

IR oracles on the cashback/holder lifetime (`pe/cbR.py`, `pe/hR.py`: recompute at the final curve stores): hL+cbR
0.56685, hL+hR 0.56466, hL+both 0.55133 (payload on r8, but the split stays on r6). An IR hoist of `new`'s piece
copies to entry (`pe/nh1.py`, `pe/nh2.py`, the original's 0x4d8-0x538) reproduces the original's `ldxw +4/+1` piece
shape, but it keeps reloading the `new` pointer instead of holding it in r7, and the tail collapses (0.477/0.434).

Side lead, off angle: main 769f331 + `hR` (the final `curve.is_holder_reward` store recomputes holder from the
argument) gives 0.6326 at 27,384 B (+4 exact, -16 B). It needs a +16 B faithful repay to be landable, and the plain source form (`hRs`) is folded back by GVN to main's bytes.

## Next ideas

- The pda front is capped at about +0.005. It is only worth collecting on top of a future tail state where `cashback`
  (or `holder`) is not a long-lived register value from validate to the curve stores. In the original those flags are
  read back or phi'd differently: r8 holds the mayhem byte at 0x2b0, and the original tail has r6/r8/r9 = sharing
  tag / pool_updated / swept. Re-screen pda as soon as a tail-RA lane lands such a state.
- An entry RA like the original's needs the `new` pointer held in r7 from 0x1e0 to 0x538. That means an entry copy of
  `new` with all pieces, together with pda. The IR hoist alone does not give it (nh2), so the copy also needs the
  sharing-pointer spill, which comes from the original's 4-callee-saved-register pressure at entry.
