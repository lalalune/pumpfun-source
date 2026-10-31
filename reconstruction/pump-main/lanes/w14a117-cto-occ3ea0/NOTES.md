# w14a117-cto-occ3ea0: the clone-run RA forces 1911/1622/1314 (a105 numbering) on ebe5387 (notes only)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main `ebe5387e1` (#3495, 0.67316 / 3,123 at 27,400). Sibling of w14a116-cto-occtail1674, which owns the tail forces.
Angle: w14a105 (#3494) climbed main 0.67226 -> 0.68005 with 8 forces. Its non-tail forces were 1911=r6 at orig 0x3ea0,
1622=r3 and 1314=r7. This lane prices them and identifies the competing vreg and the greedy step for each. It then
looks for an ordinary source form that changes that competitor's live range.
Ledger approach `occ3ea0`, keys `0x22a10-w14-ebe5387-occ3ea0-*-v1`.

**Result: no source change.** Each of the three forces is register naming at an unchanged CFG (L2 equal). Each one
traces back to a mechanism that has no source handle, or whose source family is already exhausted. Together the three
forces are worth +0.0024 at 27,400. The whole RA ceiling of the sharing clone run (orig 0x3c00-0x4800) is +0.0018.

## 1. Oracle

- Raw-IR capture of ebe5387 (`capraw.py`) + SDK `opt -O3` + llc (`rx.py`): `eq_main: true`, 0.67316 / 3,123 @ 27,400.
- Private greedy llc rebuilt from w14a84's `llc-patch/` (`build.sh`, 34 s). The w14a84 tools (`colmap.py`, `cclimb.sh`,
  `screen.py`, `climb.py`, `vname.py`, `sbs2.py`) and w14a106's `chunk.py` were copied to this lane's OUT dir with their
  paths changed.
- `tools/rl.sh` runs the private llc with the fastbuild flags. Pitfall: in zsh, an unquoted `$A` holding the flags is
  passed to llc as a single argument, which gives a wrong 28,560 B object. Use the script.
- `tools/score_o.py <o>...` prints ratio, slots, bytes and eq_main. `tools/bdiff.py a.bin b.bin` gives an L2 diff of two
  fn blobs, which finds moved blocks. `tools/p1store.py` is the IR store-motion probe in section 4.

## 2. Force prices on ebe5387 (vreg numbers moved: 963d1ee 1911 -> 1906, 1622 -> 1617, 1314 -> 1314)

| forces | ratio @27,400 | M delta (orig chunk) |
| --- | ---: | --- |
| main | 0.67316 | |
| 1906=r6 | 0.67436 | +4 (0x3800) |
| 1617=r3 | 0.67406 | +3 (0x3000) |
| 1314=r7 | 0.67346 | +1 (0x4800) |
| 1906+1617 | 0.67525 | |
| 1906+1314 | 0.67466 | |
| 1617+1314 | 0.67436 | |
| 1906+1617+1314 | **0.67555** | |
| sibling 1684=r6, 1671=r7 | 0.67795 | |
| sibling pair + this triple | 0.68035 | |
| w14a114 IR lead (TCF program rent after `_64` lifetime.start) | 0.67436 | |
| w14a114 lead + 1906 / + 1906 + 1617 / + triple | 0.67555 / 0.67645 / 0.67675 | additive |

The colour climb on ebe5387 (`data/climb-cc_main0-ebe5387.log`) chose 1684=r6, 1671=r7, 1906=r6, 1617=r3, 1706=r4,
1384=r5, 1314=r7 and 2251=r2, reaching 0.68185. A climb restricted to forces whose sites all lie in orig 0x3c00-0x4800
(`data/climb-region-*.jsonl`) chose 1906=r6, 2127=r0 and 2251=r2 and stopped at **0.67496**. The colour map rows for
that region are in `data/colmap-3c00-4800-ebe5387.tsv`.

## 3. Each force: value, competitor, greedy step

### 1906 = r6 (orig 0x3e70-0x3ea8)

- **Value.** 1906 is the load-to-store spill temp of `%294 = LDD %289, 32`, the `rent_epoch` of the **sharing
  CpiContext program clone** `a.pump_fees.to_account_info()` (`%289` = accounts+152). Siblings 1908, 1910 and 1912 are the
  temps for the flags at +40/41/42. Ours gives them r9; the original gives them r6 and spills them as ours does.
- **Competitors.** There are two:
  - 1855: the lamports Rc pointer piece of the same clone (`%291` = `[%289+8]`, sz 4,852, w 2.02e-6);
  - 1858: its key piece (`%290` = `[%289+0]`, sz 4,664, w 1.05e-6).
  Both stay live from the clone to the CpiContext construction just before the `admin_cto_sharing_config` call.
- **Greedy steps.**
  - Step 1414: 1855 takes R6, the first free callee-saved register.
  - Step 1418: 1858 takes R9.
  - Step 1486: the temps (stage 6) find no free register and evict the cheaper of the two, the key, from R9.
  - Forcing 1906=r6 evicts 1855, and 1855 then evicts 1858 from R9.
- **Equivalent forces.** 1855=r9 and 1858=r6 each give exactly 0.67436, so the gain is a swap of R6 and R9 between the
  two pieces.
  - The original's own registers lose: 1855=r0 gives 0.6474, 291=r0 0.65148 and 1858=r5 0.6499.
  - Spilling either piece loses (0.66357, 0.66197).
  - Top or bottom queue priority of 1855, 1858, 290 or 291 gives 0.638-0.673. Hints are no-ops.
- **Why the original differs.** The original keeps lamports in r0 and the key in r5, gives the temps r6, and keeps
  **swept in r9** from the sweep return (orig 0x3c40 `ldxdw r9,[r10-2088]`) to the event store (0x5030). It uses no other
  r9 in 0x3c48-0x5030. Ours spills swept's post-sweep region piece %1732 (sz 10,812):
  - at its first dequeue (step 329), %1625 gets no register;
  - at step 1238 the region split sends 1732 straight to the spill stage;
  - at step 1245 the sweep-gate flag %60 takes R9.
  With swept gone, R9 is free, so the clone pieces take R6 and R9, and the temps take whichever piece is cheaper.
  Swept is the w14a69 / w14a46 / w14a82 chain, already priced:
  - region-piece forces: 1732=r9 0.49783, r8 0.64781, r7 0.58029, r6 0.6501;
  - join piece: 1729=r9 0.51505.

### 1617 = r3 (orig 0x32e0-0x3318)

- **Value.** The `MOV 1`/`MOV 0` overflow flag of `inc_strong` in the TCF clone run (bb226-228).
- **Competitor.** None: the assignment is a free choice (`F 1617 R3 free`, no eviction), and R2 is the first free
  register in R1..R9, R0. The original's r2 is also unused in 0x3208-0x3400. Its r3 comes from the local order of the
  clone run: the original uses r0 for the lamports pointer, r5 for the count and r5 for the data pointer, where ours uses
  r5, r2 and r3.
- **Status.** This is the TCF clone-run naming cascade (#3380 tcfrescan, #3425 tcfweight, #3494). No competitor exists to
  re-spell.

### 1314 = r7 (orig 0x4bc0)

- **Value.** 1314 is `LDD %0,112`, the pool pointer, in bb42.
- **Competitor.** None: R7 is free when greedy reaches 1314. The original holds the pool pointer in r7 across the owner
  `memcmp` call because it tests the owner first. Ours tests `data_is_empty` first and reloads the pointer for the owner
  test, so 1314 is a short local and takes R1.
- **Owner-first source on ebe5387.** All of these spellings compile to byte-identical code: `n2` (owner first),
  `n2b` (`let pool=&a.pool`), `v2` (if/else) and `v3` (`!(owner!=AMM || empty)`). Each gives **0.63314 @ 27,440**.
  - The local pool code then matches the original. But MachineBlockPlacement moves a 112-instruction chain (the sweep
    `ConstraintSeeds` `with_pubkeys` `to_string` formatting blocks) from main's 0x5578 (orig 0x55b8) to just after the
    sweep call (0x3c48).
  - That costs -60 and -52 M in orig chunks 0x5000 and 0x5800, with no local gain (0x4800 chunk -6).
  - The IR block order is unchanged, so this is an llc placement decision. The llc placement options tried
    (tail-dup, exit bias, precise rotation, align) do not restore it.
- **Arm swap.** `if !pool_updated{msg!(..)}else{cpi}` is canonicalised: on main it is `eq_main`, and with owner-first it
  equals `n2`. This matches w14a106 (n2/p1/p3/p4) and w14a91 (`po`).

## 4. Live-range probes (post-opt IR + private llc; not source)

| probe | ratio | bytes |
| --- | ---: | ---: |
| store the sharing program clone pieces into the CpiContext right after the clone (data / owner / rent / flags / combos) | 0.6399 / 0.63691 / 0.63691 / 0.6409 / 0.6379-0.6401 | 27,336-27,408 |
| store only lamports early | 0.6428 | 27,408 |
| hoist the program pointer + key load into bb88 (key piece starts first, so it is larger and allocated first) | 0.66597 | 27,376 |
| hoist only the program pointer | 0.67286 | 27,400 |

The original keeps these pieces in registers until the CpiContext is built, so early stores are not its shape. The order
in MIR (lamports before key) is set by ISel and equals the original's (0x3d98 lamports, 0x3dc8 key).

## 5. w14a114 harvest (step c)

- s3 (ebe5387 block order, 4,731 rows): the best result is M 2,247, which equals main.
- i2 (ebe5387 load positions, 1,830 rows): the only lead is the TCF program literal rent load placed after the `_64`
  lifetime.start (0.67436). It lies in the orig 0x2800-0x3000 TCF run, not in 0x3c00-0x4800. It adds to this lane's
  forces (0.67675 with the triple).
- The 1906 gain keeps L2 at 0.7855, so it is not a block-order effect.

## 6. Reading / next

- What remains of main's RA ceiling outside the tail forces (1684/1671, owned by w14a116) is small: +0.0024 for the
  three forces and +0.0018 for the sharing clone-run region. Two root causes are already known dead ends:
  - swept's spill in the sharing region, where the original holds swept in r9;
  - the order of the pool tests, where owner-first triggers the block-placement move.
- Untried lead: owner-first (`n2`) is the original's local shape, but llc places the sweep `to_string` chain differently.
  If some source change elsewhere restored main's placement with owner-first, the remaining local gain would be small
  (+1 M from the 1314 force). Do not pursue it on its own.
