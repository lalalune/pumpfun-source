# w15a24-cto-raforce3: the three unowned RA-ceiling forces 1617=r3, 1906=r6, 1384=r5 (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main `9120883a9`, which has the same `programs/pump` source as `86e2a6b74` (#3666): 0.67376, 3,124 slots, 27,400 B, 1034/1034.
The capture is the w15a12 raw-IR capture `rx/m1/m.ll`, which reproduces main (`eq_main: true`). The colour map of the unedited capture is byte-identical to main's fn.
Angle: w15a14 (#3673) found a 6-force colour ceiling on main. No lane owned three of its forces: 1617=r3, 1906=r6 and 1384=r5.
For each one, find what blocks it at its greedy dequeue, then find an ordinary source lever.
Ledger: approach `raforce3`, keys `0x22a10-w15-9120883-raforce3-*-v1`.

**Result: notes only, no source change.** Each force is a register-naming choice at an unchanged CFG (L2 equal). Each one's blocker
leads into a family that is already priced as a loss: the TCF clone-run naming cascade, the `%465` `!holder` / swept family in
the sharing clone run, and the n1 event form. Note that w14a117 (#3519, on ebe5387) had already traced 1906 and 1617, under the
same vreg numbers. This lane confirms those traces on 9120883, adds the 1384 trace and the `%465` link in the 1906 chain, and
gives sticky prices.

## 1. Sticky prices on 9120883 (private RAPRIO llc with `RAPRIO_STICKY=1`)

The vreg numbering is unchanged from 90300f9 and ebe5387. `llc-patch/build.sh` is w15a18's build script: w15a12's sticky
`RegAllocGreedy.patch`, plus w15a18's `extra.py` (`RAPRIO_CASC`, `RAPRIO_WEIGHT`, spill-slot log). `slot.py` holds one
machine build slot while it builds. The build took about 1 minute; it copies the llvm-dbg build dir into this lane's `$OUT`.

| forces | ratio @27,400 | slots | L2 |
| --- | ---: | ---: | ---: |
| main | 0.67376 | 3,124 | 0.7852 |
| a = 1617=r3 | 0.67466 (+3 M) | 3,124 | 0.7852 |
| b = 1906=r6 | 0.67496 (+4 M) | 3,124 | 0.7852 |
| c = 1384=r5 | 0.67436 (+2 M) | 3,124 | 0.7852 |
| abc | 0.67645 | 3,124 | 0.7852 |
| P = 1684=r6 + 1671=r7 | 0.67855 | 3,117 | 0.7858 |
| P + abc | 0.68125 | 3,117 | 0.7858 |

- The three forces are exactly additive with each other and with P.
- Sticky and one-shot results are identical (`data/forces3-*.jsonl`), because all three intervals are local (sizes 8 to 126) and nothing evicts them.
- Sticky colour climb on 9120883 (`data/climb-sticky-9120883.log`, 122 singles, `--size 27400`) reaches **0.68244 @27,400** with 8 forces:
  1684=r6, 1671=r7, 1906=r6, 1617=r3, 1706=r4, 1384=r5, 1314=r7, 2251=r2.
  This is w14a116's ebe5387 set, with the same 8 forces, and it is the RA-only ceiling on main's code shape.

## 2. Blocker chains (RAPRIO log + `RAPRIO_TAG` asm + `regflow.py`; `data/tags-*.txt`)

### 1617=r3: TCF `pump_creator_vault_ata` clone, orig 0x32e0-0x3318 (ours 0x32d0-0x3308)

- **Value:** the `mov 1 / mov 0` overflow flag of `inc_strong` for the second Rc clone of `pump_creator_vault_ata`
  (`a.creator_vault_quote_token_account`, accounts+0x48).
- **Greedy:** step 739 logs `F 1617 R3 free`, with no eviction. R2 is simply the first free register.
- **Why the original uses r3:** in the original, r2 is live but unreferenced over the flag's range. The original clones
  lamports first (0x30f0 `[r1+8]` into r9), then loads data at 0x31b0 (`ldxdw r2,[r1+0x10]`). It keeps the data Rc pointer in r2 until the CpiContext store at 0x34c0
  (`stxdw [r10-0xc8],r2`). Ours clones data first, at 0x30d0 into r6 (`%217`, stored from r6 at 0x34b0). So in ours r2 is free.
- **Source screen (raw-IR oracle):**

  | trial | literal | bytes | ratio | 1617 |
  | --- | --- | ---: | ---: | --- |
  | c1 | `key, lamports, data (via a.cvqta), owner (via a.cvqta), ...` | 27,440 | 0.63074 | |
  | c2 | `key, lamports, data, owner` all via `x` (derive order) | 27,392 | 0.66457 | still r2: lamports goes to r6 and data to r9 (orig r9 / r2), because ours' r6 is free where the original's holds the previous clone's lamports |

  So it is the clone-run naming cascade (w14a117, #3380 tcfrescan, #3425 tcfweight). w14a17 already scanned 729 field
  placements of the TCF literals.

### 1906=r6: sharing CpiContext program clone, orig 0x3e70-0x3ea8

- **Value:** the load-to-store spill temp of `rent_epoch` of `a.pump_fees.to_account_info()` (the program `%289` = accounts+0x98).
  The flag temps 1908, 1910 and 1912 share its register. Ours puts them in r9; the original puts them in r6.
- **Greedy:** at step 1486, 1906 (stage 6, INF weight) evicts the key piece 1858 from R9.
  Forcing r6 evicts 1855, the lamports Rc pointer piece, which is sz 4,864 and lives to the CpiContext build at 0x4220.
- **Original:** it keeps that lamports pointer in **r0** (0x3d98 to 0x4298 `mov r7,r0`). So r6 is free for the temps, and swept is in r9 (w14a117).
- **New link: ours' r0 over the clone run holds a `%465` (`!holder`) split piece.** The piece is 2010, chain 2010 < 1708 < 465.
  It is reloaded at 0x3da8 (`ldxdw r0,[r10-0x908]`, an ours-only instruction). No instruction reads it before r0 is redefined at
  `ldxdw r0,[r2+32]`, so it is a dead split reload. %465 is the cashback `and` operand that MachineSink sinks to the curve store.
- **Forces along the chain (`data/chain1906-9120883.jsonl`):**

  | force | ratio | bytes |
  | --- | ---: | ---: |
  | `2127=r0` (lamports piece to r0, the original's register) | 0.67406 (+1 M) | 27,400 |
  | `2127=r0,1906=r6` | 0.67525 | 27,400 |
  | `2010=spill` | 0.67216 | 27,408 |

  With `2127=r0`, the `%465` piece moves into r6 and 1906 stays r9. The r6 occupant changes, but there is still one.
- **Status:** clearing r6 here needs both `%465` gone (w15a14 #3673: every removal loses 320+ M through a frame slot) and swept in
  r9 (w14a117 / w14a46 chain: region-piece forces 0.50 to 0.65). w15a21 priced the sharing program `let` binding (`K_sh_prog_let`):
  M 2,237 @27,424. w15a18 s1greedy priced the struct and program clone orders.

### 1384=r5: event literal, orig 0x4fe0-0x5000 (ours 0x4fa0-0x4fc0)

- **Value:** `ldxb r4,[curve+0xa5]`, an event bool, stored to `[r10-0x210]`.
- **Greedy:** step 1123 logs `R 1384 -> R4`, a free choice, because r4 and r5 are both free.
- **Original:** r4 holds `ldxdw r4,[curve+0x70]` (0x4fd8, `creator_fee_bps`), loaded at the event and stored at 0x5010 (`[r10-0x220]`).
  Ours loads it as `nf` at 0x4b80, before the pool CPI, keeps it in r9 across that CPI, and stores r9 at 0x4fd0.
- **Status:** this is exactly the **n1** form (no `nf` local). n1 gives 0.67136 @27,376 on 90300f9 (w15a04 #3700, w14a120 #3585).
  None of the 222-gene n1 screen or the w14a120 24 B repays beats main at 27,400 B, and `ev_nf_let` / `nf_blk` restore main.
  Under n1, 1384's r5 follows by itself.

## 3. Reading

- None of these three forces has a source lever outside an already-priced family. Together they are worth +0.0027 (9 M) of naming. So the
  remaining RA-only headroom on main's code shape is 0.68244 - 0.67376 = +0.0087 (8 forces). Each force is either owned
  (1684 n1event / 1671 wallet) or traced here.
- The code-shape families behind them are where the value is:
  - TCF clone order: the original clones lamports before data, with r6/r9/r2 held across the run.
  - The per-arm spilled cashback/holder phis: the original has no `%465`, so no dead r0 reload in the sharing run.
  - The n1 event read.
  Each of these costs more elsewhere on main's structure than its local naming gain.

## Files

- `llc-patch/`: `build.sh` (w15a18's, applies w15a12's sticky patch plus `extra.py`), `extra.py`, and `slot.py` (holds a machine build slot while building).
- `data/`: sticky and one-shot force grids, the sticky climb log, the 1906 chain forces, and tag dumps around each site.
- `edits/c1.py`, `edits/c2.py`: TCF `pump_creator_vault_ata` clone-order trials (EDITS format for w15a12 `cs.sh`).
- `tools/show.py`: prints screen.py results.
