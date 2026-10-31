# w15a26-cto-taiupstream: what blocks the faithful TCF program form (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 9120883a9 (origin/main e61121452 has no `programs/` change). admin_cto is 0.67376 with 3,124 slots at
27,400 B, and Pump Main is 1034/1035 normalized and raw. This lane continues w15a17-cto-tcfsroa64 (#3707), next idea 1. It
started in wave 15, died with that account at 16:09 UTC, and was finished in wave 16. Ledger approach `taiupstream`, keys
`0x22a10-w15-9120883-taiupstream-<trial>-v1` (75 rows).

**Result: notes only, no source change.** "tai" is the faithful TCF program spelling, `a.pump_amm.to_account_info()` as the
CPI program. It scores 0.6499 at 27,416 B. No upstream source form makes it pay, and neither does any register-allocation
freedom we can give it:
- 62 ordinary source forms were screened on the tai base: 20 sweep-head forms, 38 size knobs and 4 accounts-as-noalias-param
  forms. None scores above tai itself, so none comes near main.
- Under the same colour-force budget, tai's ceiling stays 0.008-0.010 below main's.
- Putting the two through-live head values at the back of the greedy queue gives the first program clone the original's
  registers, but the later clones then lose more than that clone gains.

## 1. The blocker chain at O's dequeue (tai, private RAPRIO llc, `cm/tai.ra.log`)

The register assignments in the first clone sequence (the CPI program `AccountInfo`) are:

| value | original | tai | tai vreg (root) |
| --- | --- | --- | --- |
| lamports `Rc` | r7 | r5 | `%1966` (`%129`) |
| key | r9, kept to the CPI | r4, **spilled at once** (0x2700 `[r10-0x958]`) | `%1831` (`%128`) |
| data `Rc` | r0 | r7 | `%1969` (`%130`) |
| executable (E) | r5, spilled after the payer clone (0x2838) | whole interval spilled at its def (0x2750 `[r10-0x9c0]`) | `%135` |
| owner (O) | r6, spilled after the payer clone (0x2830 `[r10-0x970]`) | r0, spilled after the payer clone (0x2810 `[r10-0x968]`) | `%1857` (`%131`) |

The original has every callee-saved register except r8 free in the run. At the TCF entry its CFG live-out is r2 and r8.
In tai, r6 and r9 are held through the whole run by two values defined at the sweep head, the same pair w15a07 named on
90300f9:
- **r6 = `%1725`**, the region-split piece (size 8,804, weight 1.51e-06) of `%121 = gep accounts, 264`, i.e.
  `&a.holder_creator_vault`. Ours spills it only at 0x3090, inside the run, and reloads it after the CPI.
- **r9 = `%1751`**, the piece (size 8,592) of `%119 = ctx.bumps.creator_vault`, which ArgumentPromotion hoists to the
  sweep head. Ours spills it at 0x30f0 and reloads it after the CPI.

The original spills both at their definitions (0x1f48 `[r10-0x8e0]` and 0x1f70 `[r10-0x910]`).

The values arrive in that order because of how greedy works through its queue (`data/trace-*.txt` holds the full log
excerpts):
1. On first dequeue (D333-D337), the run temps take caller-saved registers: lamports R1, data R3, key R2, E R4, O R5. Each
   is evicted almost at once by the next clone's temps (`%157`, `%165`, `%133`, `%138` and `%137`) and requeued for
   splitting.
2. The split queue is ordered by interval size. The head values are larger because they live across the whole run:
   `%121` 14,852 > `%60` (sweep gate) 12,730 > `%119` 12,512 > `%898` (`native`) 12,320 > lamports 9,856 > key 9,680 >
   data 9,568 > E 9,056 > O 9,024. So `%121` is split at D1233 while every run temp is still queued, and its piece
   `%1725` takes R6 over the run because R6 is free there. `%119` follows at D1264 (piece `%1751` takes R9). `native`
   (D1267) is the only head value treated as the original treats it: a short R7 piece, then spilled.
3. The run temps then split in size order, with R0-R5 and R7 left to them:
   - key keeps a piece in R0;
   - E finds no free region and is spilled whole;
   - E's INF-weight reload temp `%1764` evicts key's piece, so key ends as a short R4 piece that is stored at once;
   - O's piece `%1767` (weight 1.26e-07, so it can never evict `%1725` from R6) gets R0. `%1790`, the INF temp of the
     next clone (`%141`), evicts it again, and its last piece `%1857` stays in R0 until the post-payer spill;
   - `%1963` (an INF reload temp of a later clone's `Rc`, `%191`) evicts the lamports piece from R5. The lamports
     re-split piece `%1965` then evicts the data piece from R7. Their final pieces are `%1966` in R5 and `%1969` in R7.

So the value that holds O's register is `&a.holder_creator_vault` (`%1725`). key's register r9 is held by the bump
(`%1751`). key and E are split or spilled before O simply because their intervals are larger. Their defs, uses and
sizes are the same as in the original (w15a07), so the difference is greedy's global state, not a source construct
upstream of the run.

`data/rastate-at-O-dequeue-tai.txt` lists every register's occupants at that moment. Main's literal moves the owner load
before the Rc increments. That changes the run temps' sizes and split points: main gets lamports into r7, as the original
does, and O into r5, spilled at once.

## 2. Bounds without a source change

### Colour forces (`data/colforce-singles-tai.jsonl`, `data/cclimb-tai.log`, `data/cclimb-main.log`)

The w14a120 colmap + single-force screen + greedy forward climb, run with the private llc, gives:

| base | singles: best | climb, best at 27,400 B | climb, best overall |
| --- | --- | --- | --- |
| tai | `1966=r7` (lamports Rc to the original r7) 0.66017 @27,384; `1790=r5` 0.65948; `1857=r6` (O to r6) 0.6507 | 0.67226 (7 forces, 3,139 slots) | 0.67476 (12 forces, @27,368) |
| main | (round 1 `1684=r6`) 0.67645 @27,400 | 0.68065 (4 forces, 3,117 slots) | 0.68485 (11 forces, @27,376) |

With RA freedom tai stays 0.008-0.010 below main. Giving O the original's register (`1857=r6`) is worth +0.0008 on tai.
The faithful form's only real RA levers are lamports Rc to r7 (+0.010) and data Rc to r0 (+0.005), and main's literal
already gets the first one for free.

### Dequeue order of the head values (new, `data/raprio-last-*.jsonl`)

`RAPRIO_PRIO=<vreg>=1` puts a vreg at the back of the queue at every enqueue. This lets the run temps allocate before the
head values, which is the order the original's spill-at-def result implies.

| last in queue | tai (0.6499 @27,416) | main (0.67376 @27,400) |
| --- | --- | --- |
| `%121` (`&holder_creator_vault`) | 0.62442 @27,392 | 0.64229 @27,376 |
| `%119` (bump) | 0.60859 @27,440 | 0.62045 @27,424 |
| `%898` (`native`) | 0.6499 (no-op) | 0.67376 (eq_main) |
| `%60` (sweep gate) | 0.60416 @27,408 | 0.58055 @27,376 |
| `%121`+`%119` | 0.60997 @27,424 | 0.64141 @27,424 |
| `%121`+`%119`+`%898` | 0.61495 @27,408 | 0.6468 @27,424 |
| all four | 0.59437 @27,400 | - |

With `%121`+`%119`+`%898` last on tai, the first program clone becomes the original's: E in r5, W/S/R/O through r6, the
payer clone unchanged. With the frame masked (`FM=1 chunks.py`) the chunk deltas against tai are:

| chunk | 0x2600 | 0x2a00 | 0x2c00 | 0x3000 | 0x3200 | 0x3400 | total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| delta | +8 | +15 | -7 | -8 | -18 | -5 | 2,298 -> 2,284 |

The later clones lose more than the first clone gains. This agrees with w15a07's ABN and spill-force results on main:
the head values are where the divergence starts, but making them behave like the original is not enough.

### Block frequencies upstream of the run (`data/branchweight-tai.jsonl`)

The post-opt IR carries no `!prof` at all, so static BPI gives the TCF guard 50/50. Setting branch weights moves block
frequencies, and with them every interval's spill weight. I tried hot and cold weights (1:2000 and 1:4) on the second
`data_is_empty` branch (the TCF guard), on the `amm_present` branch, and on both. Every one re-lays blocks: 0.470-0.593
against tai's 0.6499, with TCF-region fM_oo 216 -> 257-342. The original's layout matches the unweighted guard, so this
is not where the residual is either.

## 3. Source screens on the tai base (raw-IR capture + opt/llc oracle, `tools/capvar.sh` / `tools/rx.py`)

| family | n | best | file |
| --- | ---: | --- | --- |
| sweep-head forms (`&&Context`, bump at the head, `hcv` binding, `amm_present` reuse, `dest` operand order, deref compare, late `native`, and their pairs) | 20 | 0.6499 (= tai) | `data/source-screen.jsonl` (generator `tools/gen2.py`) |
| size knobs (`sizeknobs-cto.json` + w14a73 `cat_apply.json`, applicable ones) | 38 | 0.6499 (= tai); none at 27,400 B above 0.6476 | `data/knob-screen-tai.jsonl` (`tools/gen3.py`) |
| accounts as a noalias readonly param: `fn sweep(a:&AdminCto,bump:u8,..)`, `fn sweep(a:&AdminCto,bumps:&AdminCtoBumps,..)`, a nested `fn tcf(a:&AdminCto)` for the TCF CPI, and the pair | 4 | 0.54436 | `data/noalias-screen.jsonl` (`tools/gen4.py`) |
| the same 3 noalias forms on main (reference) | 3 | 0.58476 | same |

The two `sweep(a:&AdminCto..)` spellings are byte-identical to each other. A noalias `&AdminCto` scopes every accounts
load in the sweep and re-shapes far more than the run. w15a17's joint grid (tai program x tai sub-literals) tops out at
0.65269, and its 720 tail orders and 646 owner positions at 0.6501.

## 4. Reading

- The faithful program form costs 0.024 (-79 M; -52 with the frame masked), all of it in the TCF clone-run RA cascade.
- The cascade starts where w15a07 said: `&a.holder_creator_vault` and the bump hold r6 and r9 through the run. They hold
  them because greedy's size-ordered split queue reaches them before any run temp, not because of where they are defined
  or used.
- Neither the queue order nor forced spills reproduce the original's later clones. The original's names over the eight
  clone sequences come from greedy's whole split order across the run, which depends on the whole function's interval
  sizes. Those sizes still differ from the original's elsewhere in the function (overall ratio 0.67).
- Main's TCF literal (owner loaded before the Rc increments) should therefore stay until a different function shape
  makes tai pay. Swapping it for the faithful form today costs 0.024 and 16 B.

## 5. Tools (`tools/`, experiment only)

- `capvar.sh <name> <edits.py> <slot>` / `runq.sh <slot> <names..>`: per-variant raw-IR capture (`capraw.py`, an identity
  build with `-C no-prepopulate-passes`) and the `rx.py` opt -O3 + llc oracle.
- `gen2.py`, `gen3.py`, `gen4.py`: the three tai screens above, written as exact per-line edits.
- `trace.py <ra.log> <root vreg>`: follows a vreg and its split products through a RAPRIO log (dequeues, assignments,
  evictions, spills).
- `chunks.py a.bin b.bin [step]` (`FM=1` masks frame offsets): per-original-chunk matched-token deltas.
- `fx.py`: post-opt IR edit + llc + score, with the 0x2600-0x3c00 unmatched counts.
- `slotmap.py`: aligned frame-slot map of two listings.
- External tools used unchanged: the private RAPRIO llc (`w15a24-cto-raforce3/llvmb/bin/llc`, patch in `llcp/`), and
  w14a120's `colmap.py` / `screen.py` / `climb.py` / `rastate.py` (copied into the lane OUT `ra/`).

## 6. Next ideas (outside this angle)

- tai pays only if the run's interval sizes change, and those come from the whole function. Try tai again after any
  structural change to the sweep or the function lands, since it is the faithful form. It is cheap to re-screen with
  `gen2.py`'s `p_tai.py` edit.
- The lamports Rc to r7 force (+0.010 on tai, already true on main) is the cheapest marker. A whole-sweep rewrite that
  gives tai lamports in r7 without forces is the signal to look for.
