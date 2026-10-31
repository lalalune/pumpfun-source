# w14a82-cto-walletweight: holder re-derived from the argument (0.66507 -> 0.66986) and the wallet spill-weight order (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 0d04cf460 (0.66507, 3,228 slots; post-opt IR F 0.75524, Fw 409; the w14a65 capture `base3.ll`, `eq_main: true`).
Angle: w14a65-cto-skipfreq (#3398) next idea 1, with w14a46-cto-walletcsr (#3355) and w14a35-cto-walletr8 (#3320): measure the
RAGreedy spill-weight order of the wallet's long-lived values and find the use-count/placement change that turns the
"rotation" (do_coin r9 / accounts r8 / clone buffers r7) into the original (do_coin r8 / accounts r7 / clone buffers r9).
Ledger: approach `walletweight`, keys `0x22a10-w14-0d04cf4-walletweight-*`.

**Result: landable gain, admin_cto 0.66507 / 3,228 -> 0.66986 / 3,204 at 27,400 B** (measure.sh zero losses, 1034/1034,
differential 363/0, unstripped sha 8a32bd24917d4989). The source change, found from the RA analysis (section 5): `curve.is_holder_reward` and
the event's `is_holder_reward` read the `holder: Option<bool>` argument (`holder.unwrap_or(false)`) instead of the tuple's computed
bool, which is now unused (`_holder`). The analysis behind it: the spill-weight order is measured (section 1), but it is not what decides the wallet
registers. The order of assignment is (section 2). Payload word 1 (the pointer half of the shared Err-return value, MIR `%1659`)
is in r9 across the whole original function and in r8 in ours. An IR hint that puts it in r9 adds +56 frame-masked tokens against a
same-perturbation control and halves the wallet's register diffs (section 3). No source form or zero-byte oracle gives that order
(section 4).

## 1. Spill-weight order over the wallet (`tools/llw.py`, `weights-0d04cf4.txt`)

Private copy of the debug llc (`$OUT/dbg/llc`), `-debug-only=regalloc` on the rx post-opt module. Wallet slot range = do_coin's def to +6,800
([24416, 31216)). The table lists each final piece that overlaps the range by at least 2,000 slots, its weight at its last `selectOrSplit` and its fate.

| value (MIR root) | piece | weight | fate in ours | original (orig 0x5b30-0x6b08) |
| --- | --- | ---: | --- | --- |
| accounts pointer `%0` (remainder) | %1670 | 4.3e-05 | spilled; wallet pieces r8 (clone run %1673), r7, r6 | spilled, reloaded per block from `[r10-0x8d8]` into **r7** |
| head/arg values `%466` `%382` `%385` `%389` `%383` | | 2.0e-05 - 3.3e-05 | spilled over the wallet | spilled |
| accounts copy `%62` | %1725 | 1.5e-06 | spilled | spilled |
| **sweep gate flag `%60`** | %1739 | **3.7e-06** | **r9** (evicts the tag pieces 2.85e-06 / 1.04e-08 at step 1246) | spilled at its def (`[r10-0x8e0]`) |
| `%465` (holder bool, head to post-sweep) | %1711 | 1.3e-06 | spilled | spilled |
| `%13` (holder arg) | %1704 | 1.0e-06 | spilled | spilled |
| do_collect | %1587 | 4.6e-08 | r6 | r6 |
| current_creator GEP `%71` | %1814 | 1.5e-08 | spilled (-0x920) | spilled (-0x910) |
| coin_present (`data_is_empty` r0) | %1849 | 1.9e-08 | spilled (-0x918) | spilled (-0x918) |
| **do_coin** | %1868 | **1.5e-08** | **spilled (-0x938)** | **r8** |
| tag `%59` (wallet piece) | %1714 | 1.0e-08 | spilled | spilled (-0x950) |
| clone buffers (`_130.i`, local) | %741 | 7.4e-08 | r7 | r9 |

- The wallet blocks run at about 1e-5 of the entry frequency, so every wallet-local value weighs 1e-8 to 1e-7. The flag's
  remainder weighs 3.7e-06 because its four defs sit in the hot bb26 predecessors. No use-count or use-placement edit inside the
  wallet can move a wallet value past the flag. Two orders of magnitude separate them.
- The only spill-weight inversion inside the wallet is coin_present (2.2e-08 before split) against do_coin (1.9e-08). The
  original spills both coin_present and the flag, so this inversion is not the residual.

## 2. What actually decides the wallet registers: queue order, not weight (`tools/wtl.py`, `tools/roles.py`, `timeline-0d04cf4.txt`)

Greedy dequeues the live ranges with a physreg hint first, then global ranges by size, then local ranges by position. Spill weight
only decides who may evict whom. On main:

| step | event |
| ---: | --- |
| 3 | accounts `%0` (whole function) -> r8 |
| 13 | coin_present (hint $r0) -> r7 |
| 24 | clone buffer `%741` (hint $r1, local) -> r6 |
| 311-316 | head values `%389` / `%466` / `%465` fight for r9; `%465` keeps it |
| 318 | tag `%59` evicts 9 values from r6 (clone buffer included) |
| 323 | clone buffer evicts coin_present from r7 -> **r7** |
| 331 | flag `%60` evicts the tag from r6 |
| 372 | payload word 0 `%1660` -> r7 |
| 387 | do_coin (unhinted, global, 5,808 slots): every CSR busy -> wait |
| 424 | `new` pointer `%390` (4,496 slots) evicts `%0` from r8 |
| 433 | **payload word 1 `%1659` (4,384 slots) -> r8**, which was just freed |
| 536 | do_collect -> r6 |
| 1169 | `%0` region split (split reg r8): its clone-run piece takes **r8** at step 1183 |
| 1245-1246 | flag split; the remainder evicts the tag pieces from **r9** over [18760, 33520) |
| 1426-1427 | do_coin split -> spilled: r6 do_collect, r7 clone buffer, r8 accounts piece, r9 flag |

The rotation state (`k1`+`cpm`+`g1`: flag and coin_present through slots, gate on do_coin) follows the same order up to step 1183. do_coin
then gets r9 only because the tag's wallet piece (1.0e-08) is the one thing it can evict (step 1411). So the rotation is set by the
order of hinted local / global assignments, not by spill weights. To reach the original, the clone buffer would need r9 at step 323
and the `%0` clone-run piece r7 at step 1183. Both depend on what holds r9 at steps 311-433.

## 3. The lead: payload word 1 belongs in r9 (`edits/ir/pw9.py`, `pb9.py`; `tools/regmap.py`)

Whole-function orig->ours register census over structurally aligned pairs (`regmap.py`): `r9->r7` 29 and `r9->r8` 20 lead.
The `r9->r8` substitutions are the payload word-1 loads: orig 0x1718/0x17e8/0x1b88/0x1c60 (`ldxdw r9,[r10-0x7x8]`), wallet
0x61e0/0x62c0/0x6360/0x6370/0x6a38/0x6a70. Ours has them in r8. They all sit inside the flag's range [bb26, bb35+wallet]. Because
word 1 weighs 4.3e-04, a word 1 in r9 blocks the flag remainder from r9.

Oracle: an empty `asm sideeffect "", "{rN}"` use of the Err-return pointer phi in bb67 gives word 1 a physreg hint (bit 30
priority plus the preferred register). The asm itself perturbs the function (-64..-72 B, `reorder.py` moved 9), so `{r8}` (word 1's
natural register) is the control:

| oracle | bytes | ratio | F | Fw | wallet reg diffs (wd.py) |
| --- | ---: | ---: | ---: | ---: | ---: |
| main | 27,400 | 0.66507 | 0.75524 | 409 | 53 |
| pw8 / pb8 (control) | 27,336 | 0.60888 | 0.72795 | 406 | 53 |
| **pw9 / pb9** | 27,328 | 0.62517 | 0.74486 | **426** | **29** |
| pw7 / pb6 | 27,440 / 27,488 | 0.48077 / 0.4902 | 0.522 / 0.510 | 336 / 375 | |

- pw9 vs pw8: +56 frame-masked tokens, up in 16 of 18 orig 0x400 chunks (0x1000-0x1400 +8, wallet 0x5c00-0x6800 +21).
- Under pw9 the first clone run matches the original (accounts r7, buffer r9) and so do the collection_native memcmp
  result (r9) and the payload loads. Still different: do_coin is spilled, because the unsplit flag takes r8 at step 462, and the
  second clone run still has accounts r8 and buffer r7.
- pw9 + k1 / kw / g1 / cpm (and their combinations) all score below pw9 alone (Fw 381-424).

Why word 1 lands in r8 on main: the `new` pointer `%390` (4,496 slots) is dequeued 112 slots ahead of word 1 (4,384). It evicts `%0`
from r8, and word 1 takes the freed r8 nine steps later. In the original `new` dies at entry (the entry copy of `new`, orig 0x4d8-0x538,
w14a67 #3384), so `%390` would be short. That links the wallet RA to the open entry-copy residual. Zero-byte size oracles
(`sz*.py`, empty asm MIs in a word-1 segment): +128 slots still gives r8, and +256 slots dequeues word 1 first, but it then evicts the
flag from **r6** (0.65898 @27,408), not r9.

## 4. Source and IR screens (all on 0d04cf4)

| key | what | bytes | ratio | F / Fw |
| --- | --- | ---: | ---: | --- |
| g1 | gate on do_coin only (`if do_coin{`, original form) | 27,368 | 0.66397 | 0.75420 / 405 |
| cpm | coin_present through an i8 slot | 27,424 | 0.66327 | 0.75430 / 407 |
| k1 | flag through an i8 slot | 27,408 | 0.55744 | 0.69642 / 399 |
| k1+g1 | | 27,368 | 0.55755 | 0.69664 / 398 (do_coin r9) |
| k1+cpm+g1 | rotation state | 27,400 | 0.55752 | 0.69682 / 400 |
| kw | flag through a slot across wallet() only (store bb33, reload at both exits) | 27,232 | 0.57641 | 0.66957 / 357 (r9 -> current_creator GEP) |
| kw+g1 / kw+cpm / kw+cpm+g1 | | 27,200-27,256 | 0.5761 | 0.668 / 353-355 |
| nh | new's pieces hoisted to entry as SSA (shorter `%390`) | 27,632 | 0.48173 | 0.49366 / 345 |
| nf | original-like entry copy (7 B and 9 B pieces into allocas, +8/+16 SSA) | 27,568 | 0.21532 | 0.48081 / 345 |
| wallet branch weights | 29 wallet brs x {16:1, 1:16, 4:1, 1:4} (`pair.py --single`) | | best 0.66537 / 3,228 @27,400 | F = main, Fw <= 410 |

- The +0.0003 weight pictures (bb13.i / bb24.i / bb27.i79 at 4:1) all give one 2-chain swap of the collect Err exit blocks (the
  `[r10-0x768]` reload block after the `jeq r7,2` block). The original has it before, so this is positional luck, and no source weight
  exists for it.
- The angle's source spellings: coin_present re-read per use adds `data_is_empty` calls (154+3 must stay); `if do_coin{` is g1/s1
  (w14a35/w14a46, below main); `do_collect` re-used after the coin CPI has no semantic spelling; the collect-arm clone order is
  covered by w14a20/w14a28/w14a37. None was rebuilt.
- MIR oracle (`llc -stop-before=greedy` / `-start-before=greedy`): the round trip is not exact on this main (3,325 vs 3,337
  instructions, frame offsets move), so it cannot price greedy order changes.

## 5. The landed change: holder re-derived from the argument at its late uses

The long-lived head bools hold r9 over the wallet at steps 311-316: `%389`/`%466`/`%465`, and the `holder` argument `%13`. That led to
an IR probe that ends the computed holder bool early. `hr` recomputes `(holder & -3) != 0` from the `holder` argument at the
`is_holder_reward` store (`edits/ir/hr.py`) and gives 0.67216 @27,408 (F 0.75573, M 2,244 against main's 2,220). `hr1` (`holder == 1`) gives
0.67186 @27,408. `hr3` (`holder & 1`, feeding both the curve store and the event field) gives 0.66966 @27,392. The holder argument then stays
live to the post-sweep store (its spill moves from `[r10-0x8d8]`), and the head RA cascade changes.

Source forms (`edits/src/`, raw-IR capture + rx, then measure.sh):

| key | curve store | event field | bytes | ratio |
| --- | --- | --- | ---: | ---: |
| h1 | `harg==Some(true)` (extra binding, no rename) | holder | 27,400 | = main (GVN merges it with the entry compare) |
| r1 / r3 | `matches!(holder,Some(true))` / `holder.unwrap_or(false)` | tuple bool | 27,408 | 0.60207 |
| r8 | tuple bool | `holder.unwrap_or(false)` | 27,408 | 0.60746 |
| **r5 / r6** | `holder.unwrap_or(false)` / `matches!(holder,Some(true))` | same | **27,400** | **0.66986 / 3,204** |
| r7 | `holder.unwrap_or(false)` | `a.bonding_curve.is_holder_reward` (re-read) | 27,384 | 0.66916 |

r5 is landed. The tuple's `holder` is renamed `_holder` because nothing reads it now, so the shadowed `holder` is the argument again.

## 6. Next ideas

0. On top of r5: r7 (event re-reads the curve field) is -16 B at 0.66916, so pair it with a +16 B knob. hr (the `(h&-3)!=0` recompute)
   is +0.0023 over r5 at +8 B in IR, but it needs a source spelling that GVN does not merge with the entry compare.
1. Payload word 1 in r9 is the largest register lever measured in the wallet (+0.017 F against its control). Look for source in
   which the Err-return pointer web is dequeued before the `new` pointer evicts `%0` from r8, *and* r9 is the cheapest
   eviction at that point (on main, r9 holds `%465`, 3.4e-05). The entry copy of `new` is the original's way (`%390` dies at entry).
   Pair any entry-copy spelling with the pw9 check (`regmap.py`: `r9->r8` should vanish).
2. With word 1 in r9, the flag moves to r8, unsplit, at step 462. The original spills it, so in the original at least one r6-r8
   occupant over [bb26, bb35] must outweigh 4.6e-06. Use `wtl.py <ra.log> 17000 34000 %60` on any candidate to see where the flag goes.
3. `tools/llw.py` / `wtl.py` / `roles.py` work on any debug-greedy log (`ra.sh`). `wd.py` classifies a region's aligned diffs as
   reg / frame / jump. `regmap.py` gives the orig->ours register substitution census per chunk.

## Tools (`tools/`; experiment only; run next to the w14a03/w14a35/w14a46/w14a65 tools in `$OUT/tools`)

- `wtl.py <ra.log> <lo> <hi> [roots]`: greedy timeline (step, stage, size, weight, outcome) of every vreg family over a slot range.
- `llw.py <ra.log> [lo hi minov]`: spill-weight order of the long-lived pieces over the wallet, with fates.
- `roles.py <ra.log>`: finds do_coin / do_collect / coin_present / collection_native in the pre-RA MIR and prints their timelines.
- `wd.py <dis|m.ll> [lo hi] [-v]`: aligns an orig region to the candidate structurally and counts eq / reg / frame / jump diffs.
- `regmap.py <dis|m.ll> [chunk]`: orig->ours register substitution census per orig chunk.
- `pe.sh`, `run.sh <name> <edits..>`: post-opt IR edits on `rx/base/m.ll`, then wr.py + wf2.py + wd.py in one line.
