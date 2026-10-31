# w15a07-cto-tcfthrough: the values live through the TCF clone run (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 90300f9d2. admin_cto is 0.67346 with 3,124 slots, M 2,248, at 27,400 B. Pump Main is 1034/1035 normalized and raw.
Ledger approach `tcfthrough`, keys `0x22a10-w15-90300f9-tcfthrough-<trial>-v1` (9 rows).

**Result: notes only, no source change.** The two values are named below. Every way of ending their live ranges before
the run, or of spilling them as the original does, prices below main. That holds even with the frame masked, so the bound
is negative and no source screen was warranted (the lane's threshold was +10 M).

## 1. Region numbers on 90300f9 (orig 0x2600-0x3c00, `tools/px.py`)

| mask | orig tokens left unmatched |
| --- | ---: |
| M_oo (scorer) | 216 |
| rM_oo (registers masked: frame and shape left) | 97 |
| fM_oo (frame masked: registers and shape left) | 174 |
| sk_oo (skeleton) | 26 |

These are unchanged from ebe5387 (w14a118 #3503).

## 2. The two through-live values, plus a third

At the TCF entry (`ldxdw r2,[r8+0x58]`), the CFG live-out set is r2, r8 in the original. Ours has r2, r6, r8, r9.

| ours | vreg (pre-greedy MIR) | IR value | source | original |
| --- | --- | --- | --- | --- |
| r6 to 0x30a0 | `%121` (split `%1725`, prio 0xe0002264, size 8,804) | `%330 = gep %_270, 264`: `&a.holder_creator_vault`, defined in the sweep dest check (bb83) and GVN-merged with the native arm's `&a.holder_creator_vault` | `sweep`: `a.holder_creator_vault.key()!=dest`. Later uses: `ensure_rent_exempt(..,&a.holder_creator_vault)`, `transfer_native(..,&a.holder_creator_vault,..)` and the token arm's clone | same def point (0x1f38 `mov r1,r8; add r1,264`), **spilled at def** (0x1f48 -> `[r10-0x8e0]`) |
| r9 to 0x2e80, then `mov r5,r9` / `mov r9,r5`, spilled at 0x3100 | `%119` (split `%2048`) | `%ctx.val62 = load i8, gep %ctx, 35`: `ctx.bumps.creator_vault`, hoisted to the sweep call site by **ArgumentPromotion** of `sweep(ctx:&Context,..)`. Single use: the vsigner `[bump]` store (`stxb [r10-0x4d0]`) after the TCF join | `let bump=ctx.bumps.creator_vault` | same def point (0x1d60 `ldxb r7,[r1+0x23]`), **spilled at def** (0x1f70 -> `[r10-0x910]`), reloaded at 0x2060 |
| r7, spilled at 0x1f48 | `%985` | memcmp result `%326` (`native`) | `let native=a.quote_mint.key()==native_mint::ID` | r9 (0x1df8 `mov r9,r0`), spilled at 0x1f68 -> `[r10-0x918]` |

So the original spills all three head values at their definitions, just before the `amm_present` `data_is_empty` call. Ours
keeps `&holder_creator_vault` and the bump in r6/r9 across the join and spills them only inside the run, at 0x30a0 and 0x3100.
It then reloads them after the CPI (ours-only `ldxdw r6,[r10-0x9b8]` and `ldxdw r9,[r10-0xb78]` at 0x3b80/0x3b88).
Neither the definitions nor the instruction shape differ: the difference is greedy's split/spill decision.

## 3. Pricing (post-opt IR + SDK llc, or the private RAPRIO llc; about 1 s each)

`tools/px.py <name> <m.ll> <edits.py>` applies post-opt IR edits and runs llc as fastbuild. It reports ratio, bytes, M and the
four region masks. `rx/m0/m.ll` reproduces main exactly (eq_main). The edits are in `e/lib.py`.

| trial | what | bytes | ratio | M | M_oo | fM_oo | sk_oo | whole fM |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| main | - | 27,400 | 0.67346 | 2,248 | 216 | 174 | 26 | 2,347 |
| B | re-derive the +264 GEP at its 3 later uses | 27,384 | 0.60623 | 2,023 | 426 | 174 | 26 | 2,291 |
| B1 / B2 | native-arm uses only / token clone only | 27,416 / 27,400 | 0.67056 / 0.67256 | 2,239 / 2,245 | 216 | 174 | 26 | |
| A | reload the bump at the vsigner store | 27,408 | 0.63502 | 2,120 | 326 | 237 | 34 | 2,265 |
| N | recompute `native` at the post-TCF branch | 27,432 | 0.60997 | 2,037 | 419 | 174 | 26 | 2,338 |
| ABN | all three re-derived after the join (TCF entry live-out becomes r2, r8, as in the original) | 27,432 | 0.59829 | 1,998 | 441 | 204 | 48 | 2,251 |
| tai | source: TCF program `a.pump_amm.to_account_info()` (raw-IR capture) | 27,416 | 0.64960 | 2,169 | 285 | 216 | 27 | 2,295 |
| tai+ABN | the untested combination (w14a90 tried tai with sp1/sp2 only) | 27,416 | 0.58919 | 1,967 | 468 | 230 | 29 | 2,221 |
| RAPRIO force | spill %121, %119, %1725, %2048 or %985, singly and as the trio | 27,392-27,440 | 0.619-0.644 | 2,069-2,151 | 313-384 | 174-237 | 26-34 | 2,274-2,345 |
| spd | spill-at-def through allocas (store after def, load at each use), every subset of the trio | 27,384-27,472 | 0.27-0.35 | 905-1,179 | 424-607 | 179-240 | 24-47 | 2,202-2,299 |

Reading:
- **Musical chairs (w14a79/w14a90) holds on 90300f9 for all three values.** Freeing r6 alone (B, or forcing %121) leaves the
  run's register histogram identical, because `native` (`mov r6,r0`) refills r6. Freeing r9 alone refills it the same way.
- **When all three are freed (ABN), r6/r9 do go to the clone temps the original puts there.** Orig r6 -> ours r6 rises from
  2 to 25 fields, and orig r9 -> ours r9 from 0 to 20 (`data/run-r679-confusion.txt`). Yet the other names in the run get worse:
  fM_oo 174 -> 204, skeleton +22. Register-field equality falls from 0.827 to 0.823. The removed in-run spill slots also
  shift every run frame offset (rM_oo 97 -> 310). With the frame masked over the whole function, ABN is still 96 tokens
  below main (fM 2,251 against 2,347). `data/chunkprof-ABN-vs-main.txt` gives the per-chunk deltas.
- With the original clone1 shape (tai), freeing the trio is worse still (fM_oo 230).
- An IR-level spill-at-def re-lays the whole frame, because allocas are not greedy spill slots. A greedy-level forced spill
  costs 8-24 B of frame and also never brings fM_oo below 174.

So the bound for ending these live ranges before the TCF literal, or for spilling them like the original, is **negative
under every mask**. The original's names in the run do not follow from the entry occupants alone. They follow from greedy's
whole split order over the run, which these values do not decide.

## 4. RA-only check of the run (`data/colforce-singles-90300f9.txt`)

`t84/colmap.py` (w14a84) on `rx/m0/m.ll` restricted to orig 0x2600-0x3c00 finds 655 aligned pairs and 71 vregs with 145
register misses. Each of those vregs was then forced singly to the original's register with the private llc:
- best: `%1617=r3`, the Rc `inc_strong` overflow flag at orig 0x32e0. It gives 0.67436 at 27,400 B (+3 M, M_oo 213,
  fM_oo 171) and is w14a84's `%1615` lever again;
- 10 forces are neutral and the other 60 lose.

The run's names are not reachable through RA one vreg at a time.

## 5. Tools

- `tools/px.py`: the post-opt IR oracle above. `LLC=<private llc>` with `RAPRIO_*` set selects the patched llc.
- `e/lib.py`: name-based edits that work on both the main and the tai captures:
  - `regep_auto`: re-derive the GEP at its 3 later uses;
  - `bump_auto`: reload the bump at the vsigner store;
  - `nat_auto`: recompute `native` at the post-TCF branch;
  - `spd(which,pos)`: spill-at-def through allocas.
- `tools/fscreen.sh`: one RAPRIO single force.
- `tools/lrec.py`: ledger rows.
- The raw-IR capture (`cs.sh`/`capraw.py`/`rx.py`/`mm.py`/`side.py`/`chunkprof.py`) and the colmap/vname/tagdump/regflow
  tools are w14a118's, w14a84's and w14a116's, used unchanged apart from their paths.
  The private llc came from w15a04's `llvmb` (w14a84's `build.sh`).

## 6. Next ideas (not this lane's angle)

- The run's register loss (fM_oo 174) is greedy's split order across the eight clone sequences. Region pricing says it
  cannot be reached by freeing head registers, by weights (w14a90) or by single forces. Only a different IR shape inside the
  run (clone-window source forms, w14a139) or a different frame changes it.
- `%1617=r3` is +3 M at 27,400 B with RA alone. No source form for it is known.
