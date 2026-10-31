# w15a04-cto-n1event: the n1 event form, and the owner-first pool gate as a better RA base (admin_cto 0x22a10)

Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B. Base: main `90300f9d2` (0.67346 / 3,124 slots).
Angle: continue w14a120-cto-occ4e80 (#3585). n1 drops the `nf` local, so the event reads `a.bonding_curve.creator_fee_bps`
(the original's `ldxdw [curve+0x70]` at 0x4fd8). The goal was ordinary source that makes old_fee lose r6 at the event.
Oracle: raw-IR capture + opt/llc (`rx.py`, `eq_main` true on the unedited capture) and the w14a84/w14a120 private
RAPRIO llc (`colmap.py`, `screen.py`, `climb.py`, from the w14a120 branch; the patched llc is in that lane's cache
`llvmb/bin/llc`). These are experiment tools only. Ledger: approach `n1event`, keys `0x22a10-w15-90300f9-n1event-*`.

**Result: notes only, no gain at 27,400 B.** The best zero-loss candidate at the pinned size is still main.

## 1. n1 on 90300f9

| form | bytes | ratio | event-piece force |
| --- | ---: | ---: | --- |
| main | 27,400 | 0.67346 | `1684=r6`: 0.67615 @27,400 |
| n1 | 27,376 | 0.67136 | `1682=r6`: **0.67706** @27,376 (old_fee evicted and spilled, as in the original) |

The n1 single-force screen (113 colour forces) has only one large force, `1682=r6` (+0.0057). The next ones are
`1670=r7` (post-event tail accounts piece, 0.67346) and `1680=r6` (curve-block accounts piece, 0.67326 @27,392).

## 2. Source forms tried on n1 (raw-IR oracle, all on 90300f9)

| key | form | bytes | ratio |
| --- | --- | ---: | ---: |
| rs1 / rs2 | `let reset=sharing_update.is_some()` after the sharing match / as the match value | 27,360 | 0.67066 (reset is sunk back to the event; `1682=r6` still needed) |
| sw1 / sw2 | swept kept as `Option` and unwrapped in the literal / `let swept=` direct init | 27,376 | = n1 |
| c1 / c2 / c3 | sibling `admin_cto_pool` curve form (no tuple block; old_fee after the cashback store) | 27,376 | = n1 |
| hr1 / hr2 | `let hr=holder.unwrap_or(false)` stored in the curve and passed as the pool CPI arg (the original's CPI arg is a spill reload of the stored value) | 27,408 | 0.63292 |
| p2 | pool CPI args inline (no `pargs`) | 27,408 | 0.63292 |
| pu1 | `pargs` before the pool gate | 27,440 | 0.63194 |
| n1po | owner-first gate `a.pool.owner==&AMM && !a.pool.data_is_empty()` (the original order at 0x4bc0) | 27,416 | 0.63432 |
| k1 / k2 / k3 | event literal built in a nested `fn ev(&ctx or ctx, values by value)` | 29,296 | 0.2395 |
| gene screen | n1 + each of 222 single genes from w14a109 `genes.py` | | none above n1; 27,400 only from nf-restoring genes (= main) |
| gene screen | mpo + each of 216 single genes (86e2a6b) | | none flips the pool-pointer colour (best 0.63462 @27,416) |

## 3. Why the pool-region forms drop to ~0.633, and the owner-first gate as the better base

hr1, p2, pu1, n1po (and a2/ph/po in w14a120/w14a143) all land at about 0.633. They share one RA change, not a source
layout change. On n1po the pool `AccountInfo` pointer (`%358`, loaded once at the gate as in the original) takes **r6**.
The original holds it in **r7**, because r6 holds the sharing tag there. That colour change ripples into the sweep region
(0x20c0 tag piece), and post-RA placement then moves the 108-insn 284/556 error chain from ~0x5568 (orig 0x5808) up to ~0x3c48.

| base | forces | bytes | ratio |
| --- | --- | ---: | ---: |
| n1po | `358=r7` (pool ptr) | 27,376 | 0.67256 (error chain back in place) |
| n1po | `358=r7,1681=r6` (+ event accounts piece) | 27,376 | **0.67826** (n1 best 2-force 0.67706) |
| n1po | 8-force climb (`climb-n1po-90300f9.log`) | 27,368 | **0.68577** (n1's 11-force ceiling 0.68485) |
| main+po (`mpo`, nf kept) | `359=r7` | **27,400** | **0.67466** (+0.0012 over main at the pinned size; 0.67496 vs 0.67376 on 86e2a6b) |
| main+po | none | 27,440 | 0.63344 |

So the original's gate order plus one colour (pool ptr in r7) beats main at exactly 27,400 B. Every owner-first spelling
gives the same RA: `pobind` (`let pool:&AccountInfo=&a.pool`), `pomatch` (if/else), `poc1`/`poc3` (curve block forms),
`porst` (reset early, 27,400 but 0.63511, pair-forced 0.67756), `pohr`/`pop2`/`pobind2` (break the pair force).

## 4. Per-force source-lever table (n1po climb, vreg ids on 90300f9 n1po)

| force | value | ours | orig | source lever known? |
| --- | --- | --- | --- | --- |
| 358=r7 | pool AccountInfo ptr across the owner-first gate (0x4bc0) | r6 | r7 | no: needs r6 busy across the gate (orig: sharing tag) |
| 1681=r6 | event accounts piece (0x4e80-0x50e8) | r8 | r2 then r6 | no: needs r8 busy at the event (orig: pool_updated; ours puts pool_updated in r6/r9) |
| 1669=r7 | post-event tail accounts piece (0x5cc0-0x5d78) | r8 | r7 | no (w14a139 tail colour pin family) |
| 2142=r9 | entry bonding_curve data ptr `[r8+0x38]` (0x140-0x2e8) | r7 | r9 | no |
| 1615=r3 | sweep flag phi (0x32e0) | r2 | r3 | no |
| 2084=r5 | entry `ldxb [r6+0x43e]` bump byte (0x438) | r6 | r5 | no |
| 467=r2 | validate `[r6+0x90]` chain (0x548) | r3 | r2 | no |
| 1703=r4 | curve-block holder flag `&1` (0x4a98-0x4b78) | r3 | r4 | no |

Common root: in the original, the sharing tag (`sharing_update` discriminant, `[r10-0x8f8]`) is reloaded into r6 at
0x3c58, 0x4a90 and 0x4d48 and held to its event use at 0x4f18. Greedy only splits the tag (sz ~43,900, the whole function)
in its last stage, after old_fee, the pool pointer and pool_updated already hold r6..r9 over that range, so in ours the
tag never gets the r6 region. The source has no other use of the tag in that range, and moving its test earlier
(`rs1`/`rs2`) is sunk back to the event by opt.

## 5. Next ideas

- **mpo + one size-neutral change that flips the pool pointer to r7** would land. On main 86e2a6b (0.67376), mpo is
  0.63374 @27,440, and forcing `359=r7` gives **0.67496 @27,400** (+0.0012). A screen of mpo + each of 216 single genes
  (`genescreen-mpo-86e2a6b.jsonl`) found no flip: the best is 0.63462. The lever has to be new source, not a known gene.
- Look for ordinary source that keeps the sharing tag in a register across the curve block: an early tag split, or a tag
  whose last use comes before the event. Forms the original allows: the event's `sharing_config_reset` taken from a
  value held across the pool CPI, like the original's r6 tag piece.
- n1po's 2-force base (0.67826 @27,376) is +0.0048 over main before a 24 B repay. With an ordinary pool-pointer lever,
  pair it with the w14a120 repay triples (c4/c8 cost about -0.0003 on n1).

## Tools (this dir)

- `tools/runq.sh` / `tools/capvar.sh`: copy main's crate, apply `edits/<name>.py`, capture raw IR, run rx, then `probe.py`.
- `tools/probe.py` / `tools/probe2.py`: find the event accounts piece and the pool pointer vregs from a colour map, then screen
  their forces (single and pair).
- `tools/gcap.sh` / `tools/gq.sh`: gene-screen runner (`N1`, `@edit`, gene names joined by `+`).
- `tools/regdelta.py`: per-call-segment net instruction delta vs the original (L3-masked alignment).
- `tools/mv.py`: difflib opcode diff of two fn windows (finds block moves). `tools/dis.py`, `tools/rg.py`: window dumps.
- `edits/`: every source form above. `genescreen-n1-90300f9.jsonl`, `results-90300f9.jsonl`: raw results.
