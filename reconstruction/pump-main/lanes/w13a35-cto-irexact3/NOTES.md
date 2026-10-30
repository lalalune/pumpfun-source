# w13a35-cto-irexact3: non-alloca IR-edit recipe for 0x22a10 `admin_cto::execute` on mains dfc3693 and 16c10e6

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w13a23-cto-irexact2 (#3057, `origin/swarm/w13a23-cto-irexact2-2`), whose last full scan was on 06e6bb8.
Notes only: no source change. Every number below is the post-opt `llc` oracle at 27,400 B unless noted.

## Oracle validation

| main | pre-opt IR | oracle ratio | bytes | eq_main | perfect-frame bound |
| --- | --- | ---: | ---: | --- | ---: |
| dfc3693d8 | identity build, `-C no-prepopulate-passes` (`tools/capraw.py`; copy from w13a19's capture) | 0.59916 | 27,400 | true | 0.62822 |
| 16c10e631 | same (copy from w13a39's capture, verified) | 0.62043 | 27,400 | true | 0.64949 |

`tools/rx.py` (pre-opt IR -> SDK `opt -O3` -> slim -> `llc`) gives `eq_main=true` on both. The single-edit scans run
`tools/iredit.py` on the `opt -passes=instnamer` copy of the slim post-opt module (named values let `blk` moves
renumber-free; the named module gives byte-identical output). `ir/slim*.ll` from `tools/mkslim4.py` also gives
`eq_main=true` and is what the call-site scan uses.

## Scans (ledger `0x22a10-w13-{dfc3693,16c10e6}-irexact3-*`)

Edit kinds (no alloca moves, w13a33 owns those): `bw` 1:2000, 2000:1 and 20:12 plus `inv` on all 147 condbrs,
`sz:A:+-8` on every alloca, `swapphi` on the 26 phi blocks (`tools/mkscan3.py`), and a successor layout swap per
condbr (`tools/mkblk.py`, the IR-layout effect of flipping a source `if`/`match` arm order).

| main | edits | best single at 27,400 B | greedy (size-pinned) |
| --- | ---: | --- | --- |
| dfc3693d8 (0.59916) | 1,522 | 0.60066 (+0.0015): Rc `inc_strong` trap `bw` 1:2000 (x11.i clone, `exit35.i`); `sz:sk:24` / `sz:buf.i39.i:32` | 0.60425: trap bw +0.0015, `sz:buf.i39.i:32` +0.0015, `bw:bb27.i64` +0.0009, `inv:bb47.i` +0.0006, `sz:target.i.sroa.0:15` +0.0003, `inv:bb69` +0.0003 |
| 16c10e631 (0.62043) | 1,674 | 0.62223 (+0.0018): Rc `inc_strong` trap `bw` 1:2000 (`AccountInfo::clone.exit40.i`) | 0.62403: trap bw +0.0018, `bw:bb27.i64` +0.0009, then +0.0003 steps (`sz:target.i.sroa.0:15`, `blk:bb4.i23.i:END`, `inv:bb69`) |

What each lever is, and why source cannot set it:

- **Rc `inc_strong` trap weights** (`bw` 1:2000 on the `strong==0 -> llvm.trap` edge of an `AccountInfo` clone).
  BPI already gives that edge the unreachable weight (about 1:1M); 1:2000 makes it warmer, which only renumbers
  4 deep RA spill slots (orig 0x26b0-0x2a98; abs ratio unchanged). It is std code in every clone form.
- **`bw:bb27.i64` 1:2000**: the `collect_creator_fee::collect` result `tag==2` (Err) edge. rustc attaches no weight to
  `?`; a `#[cold]` helper on the Err path is a call (size change).
- **`sz:buf.i39.i:32` / `sz:sk:24` (dfc3693 only)**: StackColoring sorts slots by size, then alloca order. The 32 B
  `sk` sorts ahead of validate's 24 B error-message `String`s (`buf.i32/39/46.i`) and of `PumpError::name()`
  results (`_56/_68/_82.i`), so it took the 48 B `authority_info.i` slot (0x518) instead of 0x470. The original has
  sk at 0x470 and a holder_key copy at 0x518 (the w13a33 hkc design). The 13-object alloca-move scan (336 edits) cannot
  reproduce it: only size decides it. On 16c10e6 (after 55d19a9, the InvalidCreator operands swapped) sk is still at
  0x518, but the same edits now lose (`sz:buf.i39.i:32` 0.61803, `sz:sk:24` 0.61983).
- **`inv`**: post-opt polarity. InstCombine folds a source-level negation back, so a negated `if` gives the same br.
- **`blk`**: none of the 294 successor layout swaps changes the output at 27,400 B. MachineBlockPlacement re-derives
  the layout, so source arm order alone (without changing data flow) is neutral here.
- **`swapphi`**: all 26 neutral.
- **Size oracle on the open frame objects (16c10e6, 504 edits, sizes 1..40 and multiples of 8 up to 64)** for
  `target.i.sroa.{0,9}`, `target.sroa.{0,8}`, `_43.sroa.11`, `event_signers.i`, `sharing_update12.sroa.3`, `target11`,
  `val6`, `hk`, `holder_key`, `_116.i`: the best is +0.0003. No object size points at a missing original object.

## Where the remaining frame headroom is (16c10e6, `tools/fbsplit.py`)

| remap | ratio |
| --- | ---: |
| none (main) | 0.62043 |
| named objects only (our offset < 0x6d0) | 0.62612 |
| spill area only (>= 0x6d0) | 0.64380 |
| every offset (perfect frame) | 0.64949 |

80% of the frame headroom is the RA spill area: from 0xb38 down, every spill slot is 8 B shallower than the original
(one more original spill slot), and 0x8d0-0xa08 are permuted by spill order. The named-object residual is the known
set (`objmap-16c10e6.txt`): `event_signers.i`/`target.i.sroa.0` (orig 0x680), `sharing_update12.sroa.3`,
`target.sroa.0` 7 B (orig 0x538/0x548), `hk`, `holder_key` (-0x18). Spill order follows register allocation,
so the next gains come from code-shape (data-flow) changes, not frame edits.

## Movescan and call-site scan

- movescan (w13a12 sinks/hoists of pure values): on dfc3693, 601 of 865 edits ran (all 125 sinks): nothing above main at 27,400 B
  (best size-changing: hoist of `%239` from bb78.i into bb24.i, 0.60015 at 27,392). The 16c10e6 rerun is in SUMMARY.json.
- Per-call-site `noinline`/`alwaysinline` (raw-IR opt oracle via `csedit.py`, 36 source-expressible sites: execute,
  wallet and sweep calls to own helpers, CPI builders, Event data and `AccountInfo::clone`): see SUMMARY.json. Each real
  inline-state change moves the size (global_quote noinline 0.57825 at 26,944 B, validate noinline 0.29849, prepare_bonding_curve
  alwaysinline 0.53472 at 28,608 B, sharing-CPI clone sites 27/31 alwaysinline 0.40/0.43 at 27,896/28,072 B). The already-inlined
  clone sites are no-ops.

## Conclusion

On both mains, no single IR edit that source can express beats main at 27,400 B, and neither does the size-pinned greedy.
Every gain the scans find comes from a branch weight with no source construct, a size class of a std/anchor temporary,
or post-opt polarity. The best of those are +0.0018 (16c10e6) and +0.0015 (dfc3693). Machine-readable ranking: `recipe.json`.

## Tools (text only, in `tools/`)

| tool | use |
| --- | --- |
| `mkscan3.py <post.ll> <prefix> [n]` | non-alloca single-edit list (bw x3, inv, sz +-8, swapphi) split into n files |
| `mkblk.py <post.ll> <prefix> [n]` | successor layout swap per condbr (needs the `instnamer` module) |
| `pscan.sh <post.ll> <prefix> <base> [n]` | run n item files as n processes (difflib is GIL-bound) |
| `omap.sh <post.ll> <spec> <dir>` | spec -> debug `llc` -> `layout.txt` + `objmap.txt` (per-object orig offset votes) in about 2 s |
| `fbsplit.py <fn.bin> [cut]` | perfect-frame bound split into named objects vs spill area |
| `rx.py`, `iredit.py`, `greedy.py`, `csedit.py`/`csscan.sh`, `mkslim4.py`, `movescan.py`, `objmap.py`, `layout.py` | from w13a23/w12a02/w13a12, repointed to this lane |
