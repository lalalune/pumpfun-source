# w14a90-cto-tcfweight: TCF clone-run spill-weight levers (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main `95a64ba75` (0.66986, 3,204 slots, 1034/1034; post-opt IR oracle `eq_main: true`, L0/L1/L2 0.66986/0.69982/0.784).
Angle: w14a79-cto-splitartifact (#3403) next ideas 1-2: change the SPILL WEIGHT (use count, placement of the last use / final
store) of the TCF clone pieces `%129` `%130` (clone1 = CpiContext program, key and lamports Rc) and the clone keys
`%137 %146 %155 %164`, instead of forcing spills. Ledger approach `tcfweight`, keys `0x22a10-w14-95a64ba-tcfweight-*`.

**Result: notes only, no gain.** On main and on the original-shape first clone (`tai`), no weight lever on any TCF piece
raises the clone-run L1 (orig 0x2800-0x4000) while keeping L2. Main is a local optimum for every final-store placement
and every extra use. The register misses follow from what holds r6/r9/r8 at the run's entry, not from the pieces' weights.

## 1. Step 1: the 160-miss table holds on 95a64ba

`blame.py` on 95a64ba, orig [0x2800,0x4000) (`data/blame-0x2800-0x4000-95a64ba.txt`): 160 register-only misses (ours-occupant
120, orig-occupant 26, free 14). The top occupants are unchanged from 0d04cf4: r6 `&holder_creator_vault` 22, r9 bump 18,
r0 clone temp 13, r8/r5 accounts pointer 10+10. `press.py` 0x2600-0x3600: mean live orig 7.21, ours 7.82. #3409 (holder arg)
did not touch this run. The MIR vreg numbers `%127-%164` are the same as on 0d04cf4.

## 2. Greedy timeline of the clone pieces (`data/greedy-tcf-95a64ba.txt`, debug llc `-debug-only=regalloc`)

Every clone piece has one def and one use (its store into `_55`, the CpiContext, in the single final block before the call),
so its weight is about 2·freq/size: the longer the range, the lighter the piece. Clone1's pieces are the longest and lightest:

| vreg | value | size (slots) | weight | fate |
| --- | --- | ---: | ---: | --- |
| %130 | clone1 lamports Rc ptr | 9,856 | 1.52e-07 | split: r7 [37152,40072), spilled after |
| %129 | clone1 key | 9,680 | 7.7e-08 | split: r5 -> r0 [37344,39320), spilled at 0x2928 |
| %128 | clone1 owner | 9,616 | 7.8e-08 | split: r0 -> r5 (328 slots), spilled at 0x2710 |
| %137 | payer key (accounts+0) | 8,544 | 8.7e-08 | r5 (328 slots), spilled |
| %146 | quote_mint key | 7,776 | 9.5e-08 | r5 (948 slots), spilled |
| %155 | token program key (accounts+32) | 7,024 | 1.05e-07 | r0 [39616,41572), spilled |
| %164 | system program key | 6,272 | 1.17e-07 | r7 (952 slots), spilled |

Ours already holds clone1's key until about the same point as the original (ours r0 to 0x2928, orig r9 to 0x2958) and the
lamports Rc in r7 (orig r7). The difference is the NAME (r0 vs r9: r9 is the bump, a head occupant) and the clone1 owner:
ours loads it in block 1 (literal owner-first, #3308/#3334) and spills it at 0x2710; the original loads it in block 3.

## 3. IR oracles (post-opt IR, llc only, ~1 s each; `tools/`)

| oracle | what | variants | best (vs main) |
| --- | --- | ---: | --- |
| `wsweep.py` (main) | for each of the ~100 pieces stored into `_55` in the final block: store at its def (`early`), at the final block's head or tail, a duplicate store in the next block (`dup`) or at the final head (`dupfb`) | 515 | no L2-neutral clone-run gain; best equal-size clone-run delta 0 (byte-near-identical tails) |
| `fuse.py` (main) | zero-byte extra use (`asm sideeffect "", "r"(V)`) of %129 %130 %128 %137 %146 %155 %164 before the br of every block from def to the call, plus an empty-asm barrier control at each point | 338 | best clone-run delta -9 (%137 at blocks 0-5, L2 = main) |
| `late.py` (main) | late reload of clone1 key/owner/rent/flags from `x.i` in the final block (singles, pairs, all 6) | 22 | all lose: best key 0.59877, L1 0.66397, clone-run -89 |
| `wsweep.py` + `fuse.py` (tai) | the same on `tai` (program = `a.pump_amm.to_account_info()`) | 240 | best clone-run sum 527 (tai 529, main 568); none above main L1 |

Per-value table: `data/weight-table-95a64ba.md`. Clone1 (main): key `%_190.i` best -10 (extra use at block 0: 0x3000 +11 but
0x2800 -22), lamports `%_224.i` best -2 (store at the tail), owner `%_189.i` -23; keys `%137/%146/%164` -6, `%155` -29.

Outliers that are not clone naming:
- `%_190.i`/`%_189.i` extra use at block 20-23 and `%_12.i.i` (tai) give L1 +0.003..+0.014 and L2 +0.012..+0.016 at
  **27,464 B**. The gain is in orig 0x800-0x1800 (chunks +29/+41): validate error blocks are placed differently (the
  `line 298` error-return block moves). It is block placement, owned by the placement lanes (w14a36, w14a71).
- `%_250.i148` (vault-authority clone lamports) stored at its def: L1 +0.0153 at 27,352 B. Chunk 0x800 +84, chunk 0x3000 -30.
  This is jump distance: the validate region's long `ja`s into the shared error tail (orig 0x5740/0x5868) match when the
  TCF region is 48 B shorter. `data/jdelta-95a64ba.txt` lists every jump pair whose offset differs (112 pairs).

## 4. Source forms (raw-IR capture + rx; `edits/`)

| key | change | bytes | ratio | L1 / L2 |
| --- | --- | ---: | ---: | --- |
| tai | TCF program = `a.pump_amm.to_account_info()` | 27,416 | 0.6475 | 0.68553 / 0.78137 |
| bindp | program literal bound to a local `p` first | 27,368 | 0.66757 | 0.69784 / 0.78058 (-32 B in the 0x3800 chunk; clone run unchanged) |
| pclone | `p.clone()` as CpiContext program, `p` as the `program:` field (extra uses of clone1's pieces) | 27,232 | 0.571 | 0.65635 / 0.73358 |

`tai` is the original's instruction shape for clone1 (orig 0x2680-0x2a00 has 0 frame/shape misses, against main's 2): key,
lamports, data, then flags 42/41/40, rent 32, owner 24. Its losses are register names only (39 against main's 19 in that window,
177 clone-run misses against 160): clone1's key is the lightest piece (7.7e-08) and is spilled at once (`[r10-2392]`), where the
original keeps it in r9 to 0x2958. The lamports Rc pointer goes to r5 instead of r7 (`data/greedy-tcf-tai.txt`,
`data/blame-0x2800-0x4000-tai.txt`).

## 5. Reading

- Weight levers are exhausted for this run. Raising or lowering one piece's weight (use count, final-store placement,
  late reload) never moves the clone-run names toward the original. It only shifts which piece is spilled, so every
  freed register is refilled. This is w14a79's musical chairs again, now for weights.
- The run's names are decided by the head occupants: r6 `&holder_creator_vault`, r9 bump, r8 accounts. Those spills
  belong to w14a86. With them fixed, `tai` (the original shape) is the base to retest. Its clone1 key needs r9 free
  when greedy reaches it at step ~1270.
- The clone run's back-jumps to the shared Rc-overflow abort (orig 0x26e0) differ by -1..-5 insns in 23 pairs
  (`jdelta`). The original has more spill stores per clone (31 artifact sites vs 22), so these jump misses go away only
  together with the spill pattern.
