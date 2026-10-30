# w14a03-cto-liverange: register-assignment / live-range census of admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 53abf28b1 (0.62672, 3,305 slots). Ledger keys `0x22a10-w14-53abf28-liverange-*-v1`.

**Result: no zero-loss gain at 27,400 B.** Every live-range lever on the values this lane owns either is byte-identical
(GVN/CSE folds it back), collapses the frame, or gains ratio only by shrinking execute (-88 to -184 B), and no size knob
set gives those bytes back. The tools and the value table below are for the other lanes.

## Tools (experiment only, under `tools/`)

| tool | what it does |
| --- | --- |
| `capvar.sh <name> <edits.py> <slot>` | w13a44 raw-IR capture (identity build with `-C no-prepopulate-passes`) + `rx.py` opt/llc oracle. The edits file may define `EDITS=[(old,new)]` and/or `T(src)->src`. `eq_main` is true on the empty edit. |
| `lr.py <rxdir> [--json]` | **value census.** Runs the debug llc (`-debug-only=regalloc,prologepilog,stack-slot-coloring`) twice: once normally and once with `-no-stack-slot-sharing`, which gives the same instructions on an unshared frame. It maps every spill/reload of ours to `SS# -> "From original %vreg" -> greedy-start MIR def (block, instr, %ir name)`. It then aligns ours against the original (difflib on n2 tokens: registers, r10 offsets, jump offsets, call/lddw immediates masked). It lists every spill and reload that only one side has, with the ours value; for orig-only rows the value comes from the nearest aligned pair of the same orig slot. It ends with per-value traffic, ours vs orig. |
| `slottab.py <ours.txt> <lr.json>` | per spill slot (r10-0x800..-0xc80): orig stores/loads, the ours slot it pairs with (votes), ours stores/loads, ours values. Slot coloring shares orig slots between values, so use `lr.py`'s per-value table for values. |
| `irre.py <m.ll> <out.jsonl> [--sub]` | **re-read oracle.** For every load in execute whose value is used in another block, it gives each using block (or, with `--sub`, each block alone) a fresh load of the same pointer right before the first use. Then llc and score. 299 variants in about 25 s. |
| `irhold.py` | the inverse: fold a dominated reload of the same pointer into the dominating load (hold a local). |
| `irremat.py` | like `irre.py` for pure values (icmp/zext/and/gep/select...): recompute the value in each using block. |
| `q.sh <slot> <list>` | queue of `name<TAB>edits<TAB>env` capvar trials -> `res.jsonl`. |

`census-53abf28.txt`, `slottab-53abf28.txt`, `irre-53abf28.jsonl` are the outputs on main 53abf28.

## Value table (main 53abf28): spill/reload traffic per value, ours vs original

Orig counts come from the nearest aligned spill/reload pair of the same orig slot, so treat them as approximate.

| value (ours vreg, source) | ours st/ld | orig st/ld | what differs | owner | lever tried here | delta |
| --- | --- | --- | --- | --- | --- | --- |
| accounts pointer `%0` (`ctx.accounts`) | 1/20 | 2/30 | orig reloads it in the clone run, 0x52e0 and 0x59d0, where ours keeps it in r6/r8 | acctlive | IR re-read in bb36 (pool_updated test) | +0.00232 @ +32 B (IR only: `ctx` is noalias readonly, so source loads are CSEd) |
| bonding-curve box ptr `%4` (accounts+56) | 1/2 | 5/9 | orig holds and reloads it, ours re-derives it from the accounts pointer | - | IR hold (fold reloads into the first load) | -0.05..-0.15 |
| holder arg `%14` (r3, Option<bool>) | 3/4 | (orig slot -0x918 is shared by 6 values) | ours tests `hopt&0xfd` twice (0x470, 0x5c0), orig tests `hopt&1` once (0x610) | - | a2 `hopt:&Option<bool>` into validate | byte-identical |
| `new` pointer `%391` | 1/2 | 2/9 | ours keeps `new` in **r9** across validate. The original copies new's pieces at entry and keeps **max_fee in r9** (orig 0x638/0x718 `mov r9,r4`, 0x1658 `jlt r1,r9`) | entrycopy (w13a41/42) | | |
| max_fee `%9` (global+1072) | 1/1 (-0x948, reload 0x15c8) | 0/0 (r9) | consequence of the row above | - | **mf1**: `CtoState.max_fee:&'g u64`, `f>*st.max_fee` | **+0.00157 @ -184 B** (IR re-read +0.00358 @ -176 B) |
| sharing_update tag `%60` (phi 2/0/1) | 8/16 | 1/16 | ours has ldx/stx re-spill pairs (0x3cc0, 0x5920, 0x5e58). In the tail the original reloads it into r6 once and uses `mov r1,r6` (0x3c58/0x3d00/0x4f18) | the -0x950 reloads before LBB0_71 align with orig's -0x950 (h2pair) | | |
| holder bool `%464` (`hopt==Some(true)`) | 1/7 (-0x908) | (no slot of its own) | ours has dead reloads at 0x3d88 and 0x4338, and at 0x4a30 ANDs it with `%465` (`skip` pieces) | sweepphi/colderr/h2pair | | |
| wallet flag `%92` (`do_coin`/`do_collect` phi) | 4/2 (-0x920) | 0/0 | **RA swap:** the original spills `coin_present` (data_is_empty r0 -> -0x918) and keeps the flag in r8. Ours keeps `coin_present` in r8 and spills the flag | - | w1-w9 statement order and spellings | best = main (w4 byte-identical; others -0.001..-0.027) |
| target.i pieces `%1579/%1580` | 1/1 | 4/4, 6/4 | original spills the validate target pieces more | validate lanes | | |

## Source and IR trials

| trial | form | bytes | ratio |
| --- | --- | ---: | ---: |
| main | | 27,400 | 0.62672 |
| mf1 | `CtoState<'g>{..max_fee:&'g u64..}`, `max_fee:&a.global.max_configurable_creator_fee_bps`, `f>*st.max_fee` | 27,216 | 0.62829 |
| mf1 + 37 size knobs (`sizeknobs-cto.json`) | best `g_rent_lam_first` | 27,224 | 0.62910 |
| stref (bools or creator by `&'g`) | CtoState layout grows 48 -> 56 B | 27,264-27,352 | 0.30-0.53 |
| gref (validate gets `g:&Global`/`c:&BondingCurve`, CtoState unchanged) | mf/he/fc/my | 27,400 | = main (GVN forwards the literal's load) |
| rmf (field removed, read via `g`/`c` at use) | best `cashback` | 27,232 | 0.62900 |
| rmf | fc / mf / he / my / combos | 27,112-27,464 | 0.605-0.628 |
| a1 `fee:&Option<u64>` / a2 `hopt:&Option<bool>` / a4 `sweep(..,holder_key:Pubkey)` | | 27,392 / 27,400 / 27,464 | 0.62532 / = / 0.38809 |
| sv/sv2/sbind (CtoState Copy by value, `&{st}`, scoped `&st` binding) | | 27,400 | = main |
| IR: target=st.creator 7-byte piece from `st` instead of the curve | | 27,376 | 0.62640 |
| IR re-read on mf1 base | accounts ptr bb32 / sharing_config ptr (accounts+144) | 27,216 / 27,224 | 0.63250 / 0.63240 (not source-expressible: no clobber between the loads) |

IR re-read scan on main (299 variants): only max_fee (+0.00358, -176 B), holder_enabled `%34` (+0.00668, -184 B; the
source forms either fold back (gref) or remove the st field (rmf he 0.61349)), is_holder_reward `%28` (+0.00044, -88 B),
`ctx.accounts` in bb36 (+0.00232, +32 B), the global data pointer in both global_quote users (+0.0006 at 27,400 B,
3,299 slots; CSEd in source) and one clone-run x pointer (+0.0008, +8 B) gain. The hold oracle (73 variants) and the
pure-value remat oracle (103) give nothing above main.

## Mechanism notes for other lanes

- The re-read gains all **shrink** execute. They remove an ours-only spill and reload, and greedy then re-splits a
  neighbour. The original has 30 more reloads and 6 more spills than main (w13a50). Moving toward fewer spills
  cannot reach 27,400 B with a gain, and pure padding loses about 0.0005 per 8 B.
- max_fee spills in ours because the `new` pointer holds r9 across validate. The original copied `new` at entry, so r9
  is free for max_fee. A faithful fix is an entry-copy form that frees r9 (w13a41: "RA-limited").
- The wallet `coin_present` vs `do_coin` register choice is the clearest single RA swap outside the owned regions. It did
  not flip under 7 statement orders. Its spill weight would need a use-count change, and the only candidate (a second
  `data_is_empty`) changes the call count.
