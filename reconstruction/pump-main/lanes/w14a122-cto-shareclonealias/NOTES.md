# w14a122-cto-shareclonealias: does aliasing decide the sharing CPI per-clone order? (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs` line 749), pinned at 27,400 B.
Base: main ebe5387 (#3495): 0.67316, 3,123 slots, M 2,247, 1034/1034. Region: the sharing CPI clone run, orig 0x3c00-0x4800.
Ledger approach `shareclonealias`, keys `0x22a10-w14-ebe5387-shareclonealias-*-v1`.

**Result: no source change, and the angle is dead.** Alias information has no effect on the per-clone order.
Stripping `!alias.scope`/`!noalias` metadata or the `noalias` attributes from the AccountInfo clone, `to_account_info`,
Rc and `AsRef` functions leaves the code byte-identical. The interleaved clone windows come only from the field order
of the literal `AccountInfo{..}` spellings in source. The faithful per-clone form does restore the original's window
map, but it loses 0.026-0.031, and the loss is spill-slot colouring in the CPI array tail.

## 1. Per-clone window map (`tools/cwin.py`, `windows.txt`)

`cwin.py <cand|orig|main|rx-name> <lo> <hi> <acc_slot>` follows the accounts pointer, each account pointer `[acc+off]` and
its Rc pointers (`[X+8]` lamports, `[X+16]` data) through registers and spill slots. It prints one line per Rc window,
from the Rc pointer load to its count store, with the account-field loads that fall inside that window. Account names:
PA pool_authority, AU authority, GL global, MI mint, SC sharing_config, EA event_authority, PR pump_fees (the program).

| window | original | main ebe5387 |
| --- | --- | --- |
| PA lamports | PR.ex wr sig rent own, **PA.key** | PR.ex wr sig rent own, **PA.own** |
| AU lamports | **PA.ex wr sig rent own**, AU.key | PA.ex **PA.key** wr sig rent, **AU.rent sig ex wr** |
| (global, Box) | GL.key, then AU.ex wr sig rent own | GL.key, AU.key, AU.own |
| MI lamports / data | MI.key / - | **MI.ex wr sig rent** / **MI.own** |
| SC lamports | MI.ex wr sig rent own, SC.key | MI.key, SC.key |
| EA | EAL, then EAD (lamports first) | **EAD first**, then EAL |
| PR lamports | EA.ex wr sig rent own, PR.key | (PRD first) EA.ex wr sig rent own EA.key |

The original is uniform for all 8 clones. In clone X's lamports window it loads the previous clone's
executable/writable/signer/rent/owner, then X.key. X's data window holds nothing. That is the derived
`AccountInfo::clone` (`to_account_info()`) order: key, lamports.clone(), data.clone(), then the remaining fields. Those
remaining fields share a block with the next clone's lamports. This is what w14a05 and w14a47 found. In main only
sharing_config (and the CpiContext program) are in that form. Each of the five literals reads some fields before its
own Rc clones, and EA and PR clone data before lamports.

## 2. Step 1: metadata and attribute oracle (kills the hypothesis)

The hypothesis was that ours proves the Rc count stores do not alias the next AccountInfo, so its field loads cross the
store, while the original's codegen behaves as if they may alias.

| trial | where | result |
| --- | --- | --- |
| strip every `!alias.scope`/`!noalias` attachment in the slim execute module, then llc | post-opt | byte-identical to main |
| strip every `noalias` param attribute, then llc | post-opt | identical (0.67316) |
| llc `-combiner-global-alias-analysis` (flag only, not source) | post-opt | 0.54227 @ 27,368 |
| v4: strip `noalias` from the params of AccountInfo::clone, to_account_info/ToAccountInfo(s), Rc clone/inc_strong, AsRef, then opt -O3 + llc | raw IR | `eq_main` true |
| v5: strip any alias metadata in raw IR (there is none before inlining) | raw IR | `eq_main` true |
| v1/v2: also strip `noalias` from execute's `ctx`/`new` | raw IR | 0.439 @ 27,496 |

Why:
- BPF llc builds the DAG without alias analysis (`useAA()` is false), so scope metadata cannot reorder anything at codegen.
- Before codegen, no IR pass hoists the field loads past the Rc stores. Post-opt IR keeps every field load where MIR put
  it, which is the source order of the literal. The window interleave is decided entirely by the literal field order.
- v1/v2: without `noalias` on `ctx`, the accounts pointer is reloaded from `ctx+8` (`ldxdw r1,[r9+8]`) before every clone,
  but the field windows are unchanged. The TCF clone run then collapses (orig chunks 0x2400-0x3c00 lose 40-58 M each).
- The original's per-clone `ldxdw rX,[r10-0x8d8]` is an RA spill. The accounts pointer `r8 = [ctx+8]` (orig 0x28) is
  stored once at orig 0x280 (`stxdw [r10-0x8d8], r8`) and the Context is not copied, so it is not an escaped or
  stack-held Context that would force memory reloads.

Step 2 (source spellings with the original's aliasing) does not apply, because no aliasing difference exists to
reproduce.

## 3. Placement bounds on ebe5387

### Cross-block field-load moves (`tools/cbmv.py`, `cbmv_top.txt`)

`cbmv.py <mn.ll> <out.jsonl> [radius] [procs]` works on the renumbered post-opt module (w14a101 `renum.py`). It moves each
of the 48 sharing-arm field loads, with its private gep, to the top or the bottom (before the terminator) of each of the
17 chain blocks, then runs llc and scores the result (px2). Each llc run takes about 0.2 s and needs no build slot.

- With all blocks in range there are 879 moves, of which 831 are valid.
- The best singles are +1 M (0.67346 @ 27,400): the CpiContext program's `executable` load `%595` placed at the bottom of
  its data-Rc block, and the sharing_config `executable` `%646` placed the same way. Together they give +2 M,
  **0.67376 @ 27,400**.
- Both are placements after the count store and before the overflow `br`. No source order can produce them, because the
  overflow branch is inside `Rc::clone`.
- Every top-of-block move, which is a source-expressible reorder between clones, is at or below main's 2,247 M. The 28
  pairs of the 8 near-neutral top-of-block moves are below main too (best 2,246).
- The +2 M pair differs from main in only 27 slots (0x3e50-0x4968), and every difference is a spill-slot offset. It is a
  spill-colouring coincidence, not structure.

### The original's canonical windows on main's module (`tools/canon.py`)

For each lamports-first literal (PA, AU, MI and the program literal x20), `canon.py` moves the key load before the lamports
store and owner/rent/flags to the top of the block after the data clone:

| variant | M | ratio | bytes |
| --- | ---: | ---: | ---: |
| main | 2,247 | 0.67316 | 27,400 |
| canon PA | 2,213 | 0.66297 | 27,400 |
| canon AU (derived field order) | 2,236 | 0.66986 | 27,400 |
| canon MI | 2,189 | 0.65598 | 27,384 |
| canon x20 | 2,166 | 0.64889 | 27,400 |
| canon all four | 2,161 | 0.64739 | 27,400 |

canon_all reproduces the original's window map exactly for PA, AU, MI and SC (`windows.txt`). The region aligns better:
- `side.py` -/+ marks in 0x3e00-0x4600 drop from 157/152 to 123/118;
- the skeleton gets 30 tokens better in 0x3e00-0x4400.

But M drops by 86. The loss is in orig 0x4200-0x4a00 (dM +25/+2/+35/+26). It is frame-only in the CPI AccountInfo array
tail (0x4800 chunk: dM +26, dfM +0): every array store reads a spill slot that is coloured differently. This matches
w14a47's tail finding. The literal orders in main are a coordinate-descent optimum that buys spill-slot coincidences
in that tail.

### Source reverts on ebe5387 (raw-IR capture + rx)

Each row reverts one sharing CPI field to plain `to_account_info()`:

| reverted field | ratio | bytes |
| --- | ---: | ---: |
| program | 0.67056 | 27,392 |
| authority | 0.66986 | 27,400 |
| pool_authority | 0.66866 | 27,400 |
| global | 0.66117 | 27,376 |
| event_authority | 0.64988 | 27,368 |
| mint | 0.64979 | 27,400 |
| all six (s1) | 0.64259 | 27,376 |

These are the same signs as w14a47 on 28ab23a. s1 is 0.031 below main.

## 4. What is left in this region

- The structural gap (159 of the 529 skeleton-masked orig-only tokens, w14a118) is the literal-vs-canonical window form.
  Closing it needs the spill-slot colouring of the field spills (the CPI array tail) and the swept/tag registers
  (w14a85: s1 has 49 ours-r9 misses where the original keeps swept in r9) to follow. Both are RA, not alias, effects.
- If a future main moves the RA of the tail (spill-slot order), re-run `canon.py` and the source reverts. canon_all is the
  cheapest probe (about 1 s) of whether the canonical form has started to pay.

## Tools (experiment only; put them next to w14a101's `rx.py`, `px2.py` (w14a114), `renum.py`, w14a118's `side.py`/`chunkprof.py`/`xled.py`/`oracle.py`/`dis.py`)

- `cwin.py`: the per-clone window map (section 1).
- `cbmv.py`: the cross-block field-load placement scan (section 3).
- `canon.py`: the original-window IR transform, run per literal and for all four. `CORD=fwd|rev` sorts the moved loads by
  derived field order. Extra arguments `unit@blk{top,bot}` apply cbmv moves together.
- `ed_noalias_*.py`: rx.py EDITS that strip `noalias` attributes (section 2).
- `batch2.sh`: capvar runs, two at a time.
