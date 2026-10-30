# w14a17-cto-sweepr0: register assignment in the sweep transfer CPI clone run (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main cef0574cf (0.63421) for the analysis and screens, re-measured on main f8dc9016f (0.63481).
Ledger: approach `sweepr0`, keys `0x22a10-w14-{cef0574,f8dc901}-sweepr0-*`.

## Result

| | main f8dc901 | this branch |
| --- | ---: | ---: |
| admin_cto ratio | 0.63481 | **0.63571** |
| slots_diff | 3,173 | 3,173 |
| bytes | 27,400 | 27,400 |
| normalized / raw | 1034 / 1034 | 1034 / 1034, 0 losses |
| differential | | 363 cases, 0 mismatches |
| unstripped sha16 | | ac7a24a99b22383e |

On cef0574 the same edit gives 0.63421 -> 0.63511.

**Change (sweep, `transfer_creator_fees_to_pump_v2`):**
`associated_token_program:{let x:&AccountInfo=a.associated_token_program.as_ref();AccountInfo{key:x.key,owner:x.owner,..x.clone()}}`
-> `associated_token_program:a.associated_token_program.to_account_info()`.

Mechanism: the hand-written form loads the ATA program's `owner` in the clone-6 block, right after the
clone-5 fields (ours 0x2bc8 `ldxdw r2,[r1+0x18]; stxdw [r10-0xaa8],r2`). The original loads it two blocks later with
the ATA flags and rent_epoch (orig 0x2d18, `ldxdw r1,[r1+0x18]; stxdw [r10-0xaa8],r1`). A plain `to_account_info()`
puts it where the original has it. `AccountInfo{key:x.key,..x.clone()}` gives the same bytes.

## Analysis on cef0574: why the clone-5 key is r5, not r0

The replanner screen's largest register-only loss is the sweep transfer CPI clone run (orig 0x2690-0x3400).
The original keeps the clone-5 key (`[r2+0]`, orig 0x2b08) in **r0** until its store at 0x31a8. Ours loads it into
**r5** (cand 0x2ac0) and spills it at 0x2c50.

Greedy chain (debug llc `-debug-only=regalloc`, `tools/occ2.py`):
1. The key is `%167 = LDD %166, 0` (range 41488-48896). Its first round fails ("wait for second round"). In RS_Split, r0 is
   the only register with positive bundles, so it is split for r0 over 26 bundles (`%1866` -> r0, tail `%1865` spilled).
2. The clone-5 `rent_epoch` (`%171 = LDD %166, 32`) is spilled. Its spill-around reload `%1898` [42208,42216) has INF
   weight, and every register is live at 42208, so it evicts `%1866` from r0. `%1866` is then reassigned to r5.
3. Occupancy at 42208 (ours): r1 clone-6 ptr, r2 clone-5 ptr, r3/r4 Rc temporaries, r5 key5, **r6 `&a.holder_creator_vault`
   (accounts+264, `%121`)**, r7 key4, r8 accounts, **r9 `bump` (`ctx+35`, `%ctx.val55`, hoisted to the sweep top)**.
   The original spills `&holder_creator_vault` (-0x8e0) and `bump` (-0x910) at the sweep top, and key3 (r6) at 0x2b80. That
   leaves r6 free for the rent scratch, so r0 keeps key5.
4. The `mov64 r0, r9` at cand 0x2e60 (orig `mov64 r9, r6` at 0x2ea0) is a split copy of the same cascade. Ours moves the bump
   out of r9 to free it for the clone-8 flags. The original moves key6 from r6 to r9.

IR bounds (post-opt `llc` oracle `tools/pe.py`, base = the main capture, `eq_main` true):

| bound | bytes | ratio | 0x2800 raw/fm/rm | note |
| --- | ---: | ---: | --- | --- |
| main cef0574 | 27,400 | 0.63421 | 162/180/250 | |
| p1: `asm sideeffect "{r0}"` use of key5 before its store | 27,432 | 0.57246 | 124/45/242 | the key spills at once; the whole run re-assigns |
| p2: p1 + the same use after the def | 27,464 | 0.56643 | 147/105/239 | |
| g1: `&holder_creator_vault` gep rematerialized at its 3 late uses | 27,376 | 0.56886 | 149/180/250 | r6 then goes to `native` (`%903`) |
| b1: bump re-read from ctx at the vsigner store | 27,408 | 0.59877 | 125/162/244 | |
| g1 + b1 | 27,368 | 0.55785 | 141/167/208 | |

The pinned-register bound is negative. Freeing r6/r9 (the values the original spills) does not hand r0 back to key5:
greedy re-cascades the run. This agrees with w13a48-cto-vaultspill: the original's early spills come from higher register
demand in its own clone run. The source value that blocks r0 is the clone-5 `rent_epoch` spill reload. It is blocked
because `bump` (r9) and `&holder_creator_vault` (r6) stay live across the run. No source form spills them without a
loss: see w13a48 for the bump-array, `slice::from_ref` and hv-binding forms.

## Clone-literal combo screen (raw-IR capture = build tokens, cef0574)

All 27 combinations of the three hand-written clones in this CPI (`tools/combo_gen.py`; results in the ledger row
`...-tf-clone-combos27-v1`):

| first `pump_amm` | ATA program | last `program:` | bytes | ratio |
| --- | --- | --- | ---: | ---: |
| main (key, owner first) | main (`key,owner,..x.clone()`) | main | 27,400 | 0.63421 |
| main | **`to_account_info()` / `key,..x.clone()`** | main | 27,400 | **0.63511** |
| main | main | owner last / natural order | 27,400 | 0.62582 |
| main | `to_account_info()` | owner last / natural order | 27,400 | 0.62672 |
| natural order / `to_account_info()` | any | main | 27,416 | 0.61965-0.62084 |
| natural order / `to_account_info()` | any | owner last / natural order | 27,416 | 0.61216-0.61336 |

The first `pump_amm` clone in natural order (s1) restores the original's clone-1 skeleton: owner loads in block 2 as at
orig 0x27a8. But it costs +16 B and 0.015, mostly as frame offsets in 0x3000.

## Tools (`tools/`, experiment only)

- `pe.py <name> [edits.py] [--base m.ll]`: post-opt IR edit -> llc -> ratio/bytes plus fm/rm/raw matched counts per 0x800
  orig chunk (`bins.json`).
- `sbs.py <cand.dis> <lo> <hi>`: orig vs candidate side by side over an orig range, aligned on the skeleton; marks register
  (R) and insert/delete (I/D) differences.
- `occ2.py <rxdir> [<ir key name>] [slot]`: from the debug-llc log, the final physreg occupancy at a slot index, with each
  interval traced back to its original vreg and MIR def.
- `combo_gen.py`, `runq.sh`: the 27-combo generator and the 2-way capvar queue.
