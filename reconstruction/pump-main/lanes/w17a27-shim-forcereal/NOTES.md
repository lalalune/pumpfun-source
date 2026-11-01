# w17a27-shim-forcereal: can the zero-footprint shim families realise main's RA headroom? (admin_cto 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Wave 17 shim track.
Base: main `53ec7fb53` (#4053): 0.68754, M 2,295, 3,096 slots, 27,400 B, Pump Main 1034/1034.
Ledger: approach `forcereal`, keys `0x22a10-w17-53ec7fb-forcereal-<item>-v1`.
Continues w17a04-shim-unlockra (#4003, weighted Rc-trap family) and w17a17-shim-docoinr8 (#4029, 1682=r7 has no lever).

**Result: notes only. The RA headroom on main is +37 M at 27,400 B (12 forces), but no cell or pair of the
zero-footprint families realises any force without a layout or frame collapse.** Two of the top three forces
(1679=r7, 1626=r3) are moved to their target register by many single cells, always together with a global cascade
(the best realising pair is 2,236 at 27,384 B; main is 2,295). The largest force (1691=r6) is moved by no cell at all. RAPRIO what-ifs give
the reason per force (section 3): only 1679=r7 has a spill-weight or dequeue-order lever, and even that lever brings a
second buffer swap in the collect event (+8 B).

## 1. Oracle

- `ir/m0.slim.ll` (pre-opt slim capture, w17a06 `capraw.py` + `preslim.py`, survivor list `surv-1647da0.txt`) and its
  post-opt slim module `fx/m0/m.ll` reproduce main exactly (M 2,295, 27,400 B, sig `61dcfe87f489`, `eq_main: true`
  against `current-baseline/unstripped.so`, for both the SDK llc and the private RAPRIO llc).
- RA tools: w16a20's private RAPRIO llc (`RAPRIO_FORCE`, `STICKY`, `PRIO`, `WEIGHT`, `HINT`, `CASC`, `TAG`), the debug
  llc for `-debug-only=regalloc`, w17a17 `occ.py` (occupancy of r0..r9 at the n-th dequeue of a vreg), w17a21
  `rvote.py` / `climb.py`.
- New here (`tools/`, experiment only). Copy them into `$OUT/tools` next to w17a21's `oracle.py`, `skel.py` and `d.py`
  (they write under the parent of their own directory):
  - `fscr.py <base.ll> <cells.jsonl> <out.jsonl> [--pre] --forces f1.bin,..`: parallel llc-only (or `--pre`: `opt -O3`
    + slim + llc) screen of IR cells. Besides M, bytes and signature it scores **force realisation**: for each forced
    output F it reports `[gained, |P|, lost, |N|]`, where P is the set of original tokens F matches and main does not,
    and N the set main matches and F does not. A cell realises F when it gains all of P and loses none of N; this is
    robust to vreg renumbering, unlike checking a vreg's register.
  - generators: `genbw.py` (`!prof` on every conditional br x p), `genlt.py` (extra lifetime.start after a START /
    early lifetime.end at block starts), `genvl.py` (load -> load volatile), `vagen.py` / `vagen2.py` (volatile
    `ctx.accounts` re-derivation in a block, w17a17's va1), w17a24's `anngen_post.py` (ptr/int annotation), w17a15's
    `ptgen.py` (passthrough, pre-opt).
  - `wif.py <m.ll> 'WEIGHT=v=*k' 'PRIO=v=p' 'FORCE=..;STICKY=1' ..`: RAPRIO what-ifs with the same force metric.
  - `climb2.py`: greedy sticky climb over a given gene list at 27,400 B. `al.py`: side-by-side cand/original view
    through an m3 alignment with RAPRIO tags. `bdiff.py`: positional diff of two candidates. `ana.py`: screen summary.

## 2. Today's force set (main 53ec7fb)

w17a21's climb (top-40 votes, K=40): 2,295 -> 2,313 at 27,400 B with 1691=r6 (+8), 1679=r7 (+7), 1626=r3 (+3);
473=r3 adds +3 at 27,392 B. Pricing **all 187 vote genes** as single sticky forces finds more (the top-40 cut misses
them), and a climb over the 20 gainful genes (`data/climb_all_53ec7fb.log`) reaches **2,332 at 27,400 B (+37)** with
12 additive forces:

| force | gain | value (ours / original) | greedy decision on main (`occ.py`, debug trace) |
| --- | ---: | --- | --- |
| 1691=r6 | +8 | event accounts reload: ours 0x4e28 `ldxdw r8,[r10-0x8d8]` before Clock::get; orig 0x4f38 `ldxdw r6,[r10-0x8d8]` after the sharing-tag test | a spill reload of `%0`, created at the very end; r6 holds the pool_updated flag phi `%1660` (it evicted `%357`, the cheapest of r6..r9) and the event_authority clone buffer `%1400`; r7 `%368` (is_holder_reward byte, read before Clock::get), r9 `%362` (`nf`, read before the pool CPI); r8 is free, so r8 |
| 1679=r7 | +7 | wallet ATA#1 accounts reload, ours/orig 0x5cc0 (orig: accounts r7, buffer r9) | the AccountInfo-array buffer `%745` is dequeued first (global, size 704 > 680), gets r6, is evicted in `%386`'s cascade, then evicts `%725` (coin data_is_empty result, w 2.2e-8) from r7; the reload is created last and r8 is the first free CSR |
| 1279=r2 | +7 | sharing clone-run Rc count temp (ours 0x44a0) | all ten registers busy; evicts `%347` from r1 (cheapest) |
| 1910=r6 | +4 | sharing CpiContext program-clone rent_epoch spill temp (INF weight) | evicts `%1869` from r9; r6 holds `%1863` (w15a24's 1906 chain) |
| 1626=r3 | +3 | TCF clone Rc overflow flag (ours 0x32c8) | r1 `%1089`, r2 free: first free; the original has the data Rc pointer live in r2 (lamports-first clone order, w15a24) |
| 1316=r7 | +2 | pool-gate `[curve+0x70]` temp (ours 0x4b88) | r1 first free; the original keeps the pointer in r7 across the memcmp |
| 1880/1881/1882=r8 | +1 each | do_coin flag spill pieces (w17a17's chain) | |
| 1741=r9, 1727=r6, 1711=r6 | +1 each | event `swept` reload; sharing-tag reloads | |
| 2152=r9 / 473=r3 | +5 / +3 | entry accounts piece / entry `[r3+24]` temp | change the size (27,384 / 27,392 B) |

## 3. Levers per force (RAPRIO what-ifs, `tools/wif.py`)

| force | spill weight of a blocker (x0.25, x4 on every interval overlapping it) | dequeue order (PRIO first/last) | other |
| --- | --- | --- | --- |
| 1691=r6 | none; also 362 x0.5/0.8, 357 x1.2/2, 1660 x0.5, FORCE 1660=r9, 362=spill: 2,286-2,295, never r6 | none | only a direct force on the reload: it evicts the flag and the buffer from r6, the flag evicts `nf` from r9, `nf` is spilled at its load (+8 B) and the buffer is spilled into -0x8d8 exactly like the original |
| 1679=r7 | **725 x4/x10 or 745 x0.2**: realised exactly, plus a second buffer swap in the wallet's collect event (0x6450, buffer r7->r8 with an extra spill): **2,297 @27,408** | **PRIO 745 last**: the same 2,297 @27,408; with FORCE 793=r7 (the collect-event buffer) it is exactly the forced output, 2,302 @27,400 | HINT 745=r8/r9: no effect / 2,175 |
| 1626=r3 | none | PRIO on the clone-run pieces 207/215/217/224/225: realised, 2,087-2,207 | FORCE 1626=r3,2194=r5: 2,255 @27,416 |
| 1279=r2, 1910=r6, 2233=r6, 1316=r7 | none | none | |

So the only force with an RA-level lever is 1679=r7, and that lever needs a second, independent change. A single
weight what-if gives the exact forced output: **WEIGHT 745 x0.2 together with 793 x5, 2,302 @27,400**. Here `%793` is
the collect-event AccountInfo buffer (bb86.i, `mov rX,r10; add rX,-0x450` before `CollectCreatorFeeEvent::data`). So
1679=r7 = the ATA#1 buffer about 5x colder plus the collect-event buffer about 5x hotter, with nothing else changed.
Branch weights cannot do that. A 3D `!prof` grid makes ATA#1 rare and the collect path hot: collection_native
(bb62.i) x coin-empty (bb13.i) x `Some` (bb84.i), 179 cells. It realises nothing, and the best cells only tie main,
because block frequencies move both buffers and every other interval together.

## 4. Family screens on main 53ec7fb (single cells, force metric)

| family | cells | identical | best M @27,400 | best any size | realise 1691=r6 | realise 1679=r7 | realise 1626=r3 |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| `!prof` on all 146 conditional brs x 9 p (models expect / expect_p) | 1,314 | 358 | 2,295 | 2,295 | 0 | 97 (best 2,231 @27,344) | 6 (best 2,020) |
| lifetime: extra start (DAG chain) / early end | 1,363 | 819 | 2,295 | 2,295 | 0 | 21 (best 1,499) | 0 |
| ptr/int annotation, post-opt (w17a24 generator) | 1,736 | 1,588 | 2,295 | 2,295 | 0 | 0 | 6 (best 2,156) |
| volatile load (read_volatile of the field) | 446 | 223 | 2,295 | 2,295 | 0 | 0 | 9 (best 2,203) |
| llvm.bpf.passthrough, pre-opt (w17a15 generator) | 1,009 | 726 | 2,295 | 2,294 @27,392 / @27,408 | 0 | 22 (best 2,207 @27,400) | 3 |
| volatile ctx.accounts re-derivation (va1) in ATA#1 / ATA#2 / event blocks | 4 + 4 hoisted | 0 | | 2,287 @27,416 | 0 | 0 (still r8) | 0 |

"Realise" = all gained tokens of the force present (or all but one). Every realising cell collapses elsewhere
(layout via MBP, or the frame via StackColoring): the force's 7-9 tokens come with a 60-800 token loss.

Concurrent lanes on the same main agree: w17a15 beam6 (1,061 pt/pb singles, best 0), w17a22 famcombos (pt, vl/rr/bw,
vs, fences, switch weights, noalias, vann; 410 combos; none above main).

Also on this main, a fine Rc-trap weight screen (w17a04's realizable family): the 42 inc_strong overflow traps of the
TCF and sharing clone runs x 22 trap probabilities from 2e-6 to 1e-2 (924 cells). 769 change code, none is above
2,295, and none realises a force.

## 5. Pairs (and triples)

- Pool: 170 cells with distinct signatures from bw/lt/an/vl: every code-changing cell at 27,400 B with M >= 2,290,
  every off-size cell with M >= 2,286 (size repair), and every force-realising cell with M >= 2,150.
- **All 14,359 pairs** (pairs that edit the same line are skipped): max **2,295**, with 528 neutral pairs at 27,400 B.
  1679=r7 is realised by 169 pairs (best 2,236 @27,384), 1626=r3 by 984 (best 2,210 @27,376, 2,205 @27,400) and
  1691=r6 by none.
- 146 passthrough pairs (pre-opt): the -8 B / +8 B complements (e.g. `pt:validate:27954` + `pt:execute:28792`) and
  the neutral cells at 27,400 B. Max 2,295 (27 neutral), and no force is realised.
- Triples: 40 random distinct-signature neutral pairs (M 2,295 at 27,400 B, changed code) x every pool cell (6,720):
  max **2,295** (1,217 neutral). 1679=r7 is realised by 40 triples (best 2,231 @27,344), 1626=r3 by 239 (best 2,203
  @27,376) and 1691=r6 by none. Main sits on a flat plateau: thousands of code-changing variants tie it and none
  climbs.

So the kill condition holds in the form that matters. No cell, pair or triple realises a force without a collapse
elsewhere, and none is above main.

## 6. Conclusions for later lanes

1. The RA headroom on main is +37 M (12 forces) at 27,400 B, double the K=40 estimate. It is real but entangled with
   code shape: 1691=r6 needs the pool_updated flag out of r6 (the original keeps the sharing tag in r6 across the pool
   CPI and Clock::get, reads `nf` and is_holder_reward after Clock::get, and keeps the Result payload local, in r1);
   1626=r3 needs the lamports-first clone order; 1279=r2 and 1910=r6 sit in the sharing clone run where all ten
   registers are live.
2. Zero-footprint constructs act on these intervals only through spill weights, block placement, the DAG chain and
   IR folds. Section 3 shows that spill weight and dequeue order are not levers for any force except 1679=r7, and
   section 4 that every cell which moves 1679=r7 or 1626=r3 moves the layout or the frame as well.
3. 1679=r7 is the one force with a clean RA lever (`%745` dequeued after the reload, or lighter than `%725`). Its
   second half is the collect-event buffer `%793`. A construct that changes only the ATA#1 buffer's priority (its
   interval size: today 704 slots vs the reload's 680) would need a source change that lengthens the accounts reload
   or shortens the buffer, with no other effect. The volatile re-derivation (va1) makes the accounts value an ordinary
   vreg, but it is still dequeued after the buffer (size 720 < 736) and lands in r8.
