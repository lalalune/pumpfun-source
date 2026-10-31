# w14a106-cto-earlyload: load-provenance table for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. This lane continues the
nf early-read lead (w14a86 #3437, w14a80 #3411). Ledger approach `earlyload`, keys `0x22a10-w14-<main7>-earlyload-<trial>-v1`.
Main moved from 963d1ee (0.67226, M 2,244) to 13fe453 (#3480, 0.67256, M 2,245) during the lane. Oracle: raw-IR capture +
opt + llc (w14a70 `capvar.sh` / `rx.py`). `m0` reproduces main exactly (`eq_main`) on both bases. M = matched masked tokens.

## Tool: `tools/prov.py` (load provenance)

`prov.py <fn.bin|orig> [--opt]` runs a forward dataflow pass over the sBPF function. Each register and r10 stack slot holds a
symbolic pointer expression rooted at the entry registers. Every `ldx` whose base is not r10 is recorded as
`<expr>.<off>[:w|h|b]` with all of its offsets in the function. The roots are:

| root | meaning |
| --- | --- |
| `R2` | `&Context`; `R2.8` is `ctx.accounts` |
| `R2.8.<k>` | the account field at accounts+k. Examples: `38` bonding_curve Box, `8` global Box, `90` sharing_config, `70` pool, `a0` pump_fees_event_authority. Inline AccountInfos sit at `d8..102` |
| `R5.-ff8` | the `new: Option<Pubkey>` stack argument (tag at +0, key at +1) |
| `R5.-1000` | the `fee` stack argument |

The analysis has two modes:
- Strict (default): the meet keeps only values that agree on every path.
- `--opt`: values that are unknown on one path are ignored. It recovers more reads, but it invents a few chains after
  stack-slot reuse, for example `R2.8.98.8.78.*` and `R2.8.90.0.0.*`.

`provtab.py a.json b.json [min_delta_hex]` joins two runs by expression. `chunk.py ref.bin cand.bin...` gives per-0x800
matched-token deltas. `PROVTAB-13fe453.txt` is the strict table of the original against main 13fe453. Its columns are:
orig first offset, ours first offset, delta, expr, read counts, all offsets.

## What the table shows (main 13fe453)

All 213 load expressions were compared. Outside the cases below, every load from ctx, accounts or the args has the same read
count as the original. Its first read sits within ±0x50 of the original's, which is the accumulated size drift.

**Reads the original makes earlier (or reads that only the original makes):**

| value | original | ours | status |
| --- | --- | --- | --- |
| holder-rewards PDA before `shared` | FPA at 0x80, sharing key copy and memcmp(curve+8, sk) at 0x148-0x1c8 | shared first (0x80-0xf8), FPA at 0x1a8 | hk-first collapses (w14a04, w14a09, w14a11; w14a93 screened every head order on 963d1ee) |
| curve bools a3 (cashback), a5 (holder_reward), a2 (mayhem) before quote_mint | 0x290-0x2b0 | 0x450-0x460 (after the quote chain) | flaghoist collapses (w14a04, w13a41, faf9962 derefreread; w14a93 on 963d1ee) |
| global Box pointer `accounts+8`, loaded once and held | 0x288 (r6) | 0x380 and 0x420 (2 loads) | **g1/g2/g3 here: M 2,108 @27,328 (-136), the TCF-run RA cascades** |
| `new` key pieces (+1:w, +4:w, +8, +0x10, +0x18, +0x20:b) | entry 0x4d8-0x538, then the +1/+24 7/9 pieces in validate 0xc20-0xc50 | +1 as 4 dwords read **3 times** (0xbb8, 0x1370, 0x1830), +8.. at 0x1438 | entry copy collapses (w13a41, w14a67, w14a82) |
| creator copy through a materialised `curve+8` GEP | `add64 r9,8` at 0x358 (quote block), copy at 0x468 | offsets folded into the loads at 0x3d8 | **c1/c3 here: byte-identical (CGP folds the GEP)** |
| shared-arm `target` = st.creator from the CtoState slot | 0xdc8-0xe10 reads [r10-0x38..-0x20] | re-reads the curve as a 7/25-byte piece copy at 0x1870 (`+8.0:w +8.3:w .f .17 .1f .27:b`) | **t1 here: -3 M @-8 B**. The first 7 bytes are still forwarded from the curve (GVN memcpy forwarding) |

**Reads ours makes that the original does not (the original uses a held value):**

| value | original | ours | status |
| --- | --- | --- | --- |
| pool CPI `is_holder_reward` arg | r4 = phi slot [r10-0x950] (per-arm constants stored at 0xe40/0x1130/0x14e0/0x1830/0x18b0) | re-reads curve+0xa5 at 0x4c20 | **h2 here: -343 M**; arg forms collapse too (w14a107 pa_hb/pa_hopt) |
| curve store `is_holder_reward` | the same [r10-0x950] slot, no `and 1` | `holder.unwrap_or(false)` = [r10-0x8e8] & 1 | **h1 (`_holder`) here: -43 M @+8** |
| `nf` (new creator_fee_bps) | read inside the event at 0x4fd8, next to the a5/a3 re-reads | early read at 0x4b80, held in r9 (w14a86) | **n1 here (event reads the curve again): -8 M @-24 B** |
| pool pointer `accounts+0x70` | 2 loads: owner memcmp first, then data_is_empty on the held r7 | 3 loads: data_is_empty first | **every owner-first or non-short-circuit form moves a 109-instruction block (n2/p1/p3/p4: -132..-222 M)**; `let pool=&a.pool` is byte-identical (p5) |
| sharing event_authority pointer `accounts+0xa0` | 1 load; lamports, then key, then data | 3 loads; data first | literal order converged (w14a30, w14a43, w14a23; eperm 720 orders) |

The sharing and TCF CPI clone runs differ only in where `rent_epoch` and the flags are read relative to the Rc clones (0x100-0x140
apart). Those literal and Rc orders are a proven local optimum (shareauthport rounds 6-7, tcflit pp/place, s1colour lattice).

## Trials (oracle; none beats main)

| trial | base | bytes | M | Δ M vs main |
| --- | --- | ---: | ---: | ---: |
| t1 `target=st.creator` (r tuple kept) | 963d1ee | 27,392 | 2,241 | -3 |
| t1b `target=st.creator;(false,Some(args.0),true)` | 963d1ee | 27,408 | 2,242 | -2 |
| c1 / c3 `let cr=&a.bonding_curve.creator`, `creator:*cr` | 963d1ee | 27,400 | 2,244 | 0 (identical) |
| g1 / g2 / g3 / cg `let g:&Global=&a.global` before quote_locked | 963d1ee | 27,328 | 2,108 | -136 |
| n1 nf read back inside the event | 13fe453 | 27,376 | 2,237 | -8 |
| n4 nf after pool_updated | 13fe453 | 27,424 | 2,237 | -8 |
| n2 pool owner test first / n3 n1+n2 | 13fe453 | 27,440 / 27,416 | 2,113 / 2,115 | -132 / -130 |
| p1 owner read into a local first / p3 `&` / p4 owner `&` empty | 13fe453 | 27,608 / 27,480 / 27,472 | 2,023 / 2,110 / 2,111 | -222 / -135 / -134 |
| p5 `let pool=&a.pool` | 13fe453 | 27,400 | 2,245 | 0 (identical) |
| h1 curve store from `_holder` | 13fe453 | 27,408 | 2,202 | -43 |
| h2 pargs.1 from `_holder` / h3 both | 13fe453 | 27,448 / 27,472 | 1,902 / 2,069 | -343 / -176 |
| G1 (g1 on 13fe453): global ptr loads now 0x268/0x4028 = original count and placement | 13fe453 | 27,328 | 2,109 | -136 |
| GF / GFc / FG: g binding + curve bools first (original head read order minus PDA) | 13fe453 | 27,352 | 2,095 | -150 |
| F0: curve bools first (flaghoist) | 13fe453 | 27,352 | 2,112 | -133 |
| GP: g binding + PDA first / GPF: + bools first (full original head read order) | 13fe453 | 27,400 / 27,344 | 1,953 / 1,957 | -292 / -288 |
| GT: G1 + t1 | 13fe453 | 27,320 | 2,110 | -135 |

No trial can be repaid at 27,400 B. The pure ±8 B size shift on this main is worth at most +1 M (w14a80 section 8), while the
cheapest trial that changes bytes (t1b) is -2 M at +8 B.

## Skeleton view (`tools/skel.py`): the head read order is right, the registers are not

`skel.py` matches instructions against the original at three masking levels:
- L0: immediates and jump targets masked;
- L1: also r10 offsets masked;
- L2: also register numbers masked, which leaves the instruction-selection and block skeleton.

| variant (13fe453) | L0 | L1 | L2 | L2 delta |
| --- | ---: | ---: | ---: | ---: |
| main | 2,271 | 2,509 | 2,787 | 0 |
| G1 (global held) | 2,142 | 2,439 | 2,787 | 0: a pure RA/frame cascade (register-masked diff vs main is renames in the TCF run 0x2800-0x3800) |
| F0 (bools first) | 2,144 | 2,374 | 2,849 | +62 |
| GF (global held + bools first) | 2,125 | 2,379 | 2,859 | +72 |
| GP (global held + PDA first) | 1,991 | 2,261 | 2,807 | +20 |
| **GPF (full original head read order)** | 1,995 | 2,428 | **2,883** | **+96** |
| t1 / n1 / h1 | 2,271 / 2,265 / 2,232 | | 2,784 / 2,786 / 2,784 | -3 / -1 / -3 |
| n2 / p1 / h2 / h3 | | | 2,687 / 2,698 / 2,682 / 2,680 | about -100 (block layout) |

L2 deltas per original 0x800 chunk:
- PDA-first gains +36..+40 in the entry chunk 0x0-0x800.
- **Bools-first gains +58 in the sharing CPI chunk 0x4000-0x4800.** On main, difflib aligns a 138-instruction clone run at cand
  0x3f28 that the original has at 0x4050: main lays the first sharing clone run one block early. F0 restores that order. The
  likely route is that the cashback/holder flag live ranges change where MachineSink and block placement put that block
  (compare w14a29 hcbools).
- GPF loses -12 in 0x3000-0x3800 (the TCF run).

So the original head read order (PDA first, global pointer held, curve bools before the quote chain) is the faithful skeleton,
worth +96 L2 tokens. Every version of it loses 130-290 real tokens to register and frame assignment. That is the same cascade
w14a09 (pdara) and w14a93 (pdaheadra, 0.58906 -> 0.65806 with 11 RA forces) priced. A source route to GPF's skeleton with
main's register assignment would be the largest open lead in the head.

## Re-check on main ebe5387 (#3495, 0.67316, M 2,247)

`m0` is `eq_main`. Each rerun on the new main loses the same amount as on 13fe453, and skel.py L2 values are identical:

| rerun | bytes | M | M delta | L2 |
| --- | ---: | ---: | ---: | ---: |
| t1 | 27,392 | 2,244 | -3 | 2,787 |
| F0 | 27,352 | 2,114 | -133 | 2,849 |
| GF | 27,352 | 2,097 | -150 | 2,859 |
| GP | 27,400 | 1,956 | -291 | |
| GPF (with the #3495 sk-local `shared`) | 27,344 | 1,960 | -287 | 2,883 |

## Conclusion

The early-read mechanism is exhausted on 13fe453. Every value the original reads earlier is in the head cluster (0x0-0x540:
PDA order, curve bools, global pointer, `new` pieces), and moving any of them alone or in any order triggers the known
whole-function RA cascade. The w14a93 head screen covered every order. The remaining provenance differences go the other way:
the original passes a phi slot where we re-read the curve (holder), or it reads late where we read early (nf). Each of these
changes block layout (pool test) or register assignment by more than any size knob can repay. The next gains need
code-shape changes, such as the holder per-arm phi slot together with its consumers, and not read placement. GPF (+96 L2) is the
head skeleton to keep if an RA-side lever is ever found.
