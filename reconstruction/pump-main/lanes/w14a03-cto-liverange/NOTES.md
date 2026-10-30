# w14a03-cto-liverange: register-assignment / live-range census of admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 53abf28b1 (0.62672, 3,305 slots). Ledger keys `0x22a10-w14-53abf28-liverange-*-v1`.

## Tools (experiment only, under `tools/`)

| tool | what it does |
| --- | --- |
| `capvar.sh <name> <edits.py> <slot>` | w13a44 raw-IR capture (identity build with `-C no-prepopulate-passes`) + `rx.py` opt/llc oracle. Edits file may define `EDITS=[(old,new)]` and/or `T(src)->src`. `eq_main` is true on the empty edit. |
| `lr.py <rxdir> [--json]` | **value census.** Runs the debug llc (`-debug-only=regalloc,prologepilog,stack-slot-coloring`) twice, once with `-no-stack-slot-sharing` (same instructions, unshared frame), and maps every spill/reload instruction of ours to `SS# -> "From original %vreg" -> greedy-start MIR def (block, instr, %ir name)`. Then aligns ours against the original (difflib on n2 tokens: registers, r10 offsets, jump offsets, call/lddw immediates masked) and lists every spill and reload present on one side only, with the ours value (orig-only rows use the nearest aligned pair of the same orig slot). |
| `slottab.py <ours.txt> <lr.json>` | per spill slot (r10-0x800..-0xc80): orig stores/loads, the ours slot it pairs with (votes from aligned equal spill/reload pairs), ours stores/loads, ours values. |
| `irre.py <m.ll> <out.jsonl> [--sub]` | **re-read oracle.** For every load in execute whose value is used in another block, give each using block (or, with `--sub`, each block alone) a fresh load of the same pointer right before its first use, llc, score. 299 variants in ~25 s. |
| `q.sh <slot> <list>` | queue of `name<TAB>edits<TAB>env` capvar trials -> `res.jsonl`. |

`census-53abf28.txt`, `slottab-53abf28.txt` and `irre-53abf28.jsonl` are the outputs on main 53abf28.

## Value table (main 53abf28)

Spill-slot traffic, orig vs ours (stores/loads), slots paired by aligned spill/reload votes:

| value (ours vreg, source) | orig slot st/ld | ours slot st/ld | owner / lever tried | delta |
| --- | --- | --- | --- | --- |
| accounts pointer `%0` (`ctx.accounts`) | -0x8d8 2/32 | -0x8e0 1/20 | acctlive. IR re-read of `ctx.accounts` in bb36 (pool_updated test) | +0.00232 @ +32 B (IR only; ctx is noalias readonly, so source loads CSE) |
| sharing_update tag `%60` (phi of 2/0/1) | -0x950 8/18; tail reloads into r6 from -0x8f8 | -0x8e8 9/18, plus ldx/stx re-spill pairs at 0x3cc0, 0x5920, 0x5e58 | h2pair (-0x950) | - |
| bonding_curve data ptr `%4` (accounts+56) | -0x8e0 6/16, -0x8f8 5/10 | -0x900 5/9 | IR re-read: no gain | 0 |
| quote_locked `%7` | -0x910 4/10 | -0x918 5/9 | | |
| `new` tag byte `%16` | -0x918 9/9, -0x928 3/7 | -0x938 4/8 | | |
| holder bool `%464` (hopt==Some(true)) | no orig slot | -0x908 1/7 (ours only; dead reloads at 0x3d88, 0x4338) | | |
| shared/skip partial `%465` | no orig slot | -0x8f8 2/1 (ANDed with `%464` at 0x4a30) | sweepphi/colderr | |
| holder Option arg `%14` (r3) | no orig slot | -0x8d8 4/5 | | |
| max_fee `%9` (global+1072) | none: orig holds it in r9 at the fee test (0x1658 `jlt r1, r9`) | -0x948 3/5 (reload at 0x15c8) | **re-read at use**: `CtoState.max_fee:&'g u64` (mf1) | +0.00157 @ -184 B (IR: +0.00358 @ -176 B) |
| target.i.sroa.7/.8 `%1579/%1580` | -0x948 4/3, -0x998 2/3 | -0x970 2/3, -0x978 2/3 | validate lanes | |
| clone-run fields (`%129..%348`) | -0x990..-0xc38 1-2/1-3 each | same pattern, mostly 1:1 | acctlive | |

## Findings

- The original has 31 more reloads and 6 more spills than main (w13a50 histogram). By value, ours has **fewer** reloads
  of the accounts pointer (20 vs 32) and of the bonding-curve pointer (9 vs 26 over two orig slots), and **more** of the
  holder bool (-0x908, a slot the original does not have) and the max_fee value (the original keeps it in r9).
- IR re-read scan (299 variants): only max_fee (+0.00358, -176 B), `ctx.accounts` in bb36 (+0.00232, +32 B), the global
  data pointer in the global_quote users (+0.0006 at 27,400 B, 3,299 slots) and one clone-run pointer (+0.0008, +8 B)
  gain. Everything else is <= 0 or the +8 B noise (+0.00021).
- Source: making `CtoState.max_fee` a `&'g u64` (`e/mf1.py`) realizes the max_fee re-read: 0.62829 at 27,216 B.
  Every other CtoState field as a reference (`e/stref.py`, bools and creator) collapses the ratio to 0.30-0.53
  (CtoState layout change moves the frame).
