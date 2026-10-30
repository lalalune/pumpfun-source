# w13a40-cto-clonera7fb: why the sharing-CPI clone run keeps the accounts pointer in a register

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: continue w13a09-cto-cpiclone (#2904) next_ideas 1 and 2: diff the regalloc of the 6/2 build
`w10r1-admincto-hillclimb/hc/keep/7fb9a5e3e7a2` against main, and screen the 6/2 builds' genes on current main.
Bases: main 16c10e631 (0.62043, 3,306 slots) for all trials; main moved to 52c0b087c (0.62103) during the lane.
Scratch: `~/.cache/pumpfun-reconstruction/lanes/w13a40-cto-clonera7fb/` (not in git).
Ledger: approach `cpi-clone-placement`, keys `0x22a10-w13-16c10e6-clonera7fb-*`.

No source change is proposed. This PR holds the mechanism, the oracles that show it, and the trial tables.

## 1. Result: the clone-run register allocation is set by swept / Err-payload coalescing

`tools/clonefeat.py` spill/reg: the original is 6/2, main is 2/6. Main reloads the AdminCto accounts pointer once
(`ldxdw r5,[r10-0x8e8]`) and keeps it in r5 for all 8 clones. The original reloads it from `[r10-0x8d8]` for each account.

The debug llc (`~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc -debug-only=regalloc`, byte-identical object to
the SDK llc) shows the same two-step chain in the 6/2 build and in main:

| step | 7fb9a5e3e7a2 (reconstructed, cf 6/2) | main 16c10e6 (cf 2/6) |
| --- | --- | --- |
| Err-payload class (vreg with the `LDD %stack.N, 8` Result-payload loads) | `%1668`, 27 loads, **includes `swept`** (`MOV_ri 0` on the skip path, AdminCtoEvent store at +184) | `%1658`, 22 loads, swept is a separate vreg `%1629` (spilled to `[r10-0x968]`) |
| payload class register | **r9**, live from the first Err site to the exit, so across the clone run | r8 |
| accounts pointer `%0` region split (RAGreedy `tryRegionSplit`) | `Split for $r9 in 57 bundles`: r9 is busy in the clone run, so the clone-run blocks fall into the stack complement and every use is reloaded (6/2) | `Split for $r6 in 96 bundles` + compact region: r6 is free in the clone run, so the clone run becomes one interval (`%1686`, 8 uses), assigned r5 (2/6) |

The original matches the 7fb9 column. w13a36 (#3133) found that the original keeps `swept` and the global Err payload in r9.
This trace shows that r9 is also why the clone run reloads the pointer.

### Why swept does not coalesce on main

RegisterCoalescer (`joinAllIntervals`) visits blocks in `MBBPriorityCompare` order. All blocks are at loop depth 0, so the
order is critical-edge blocks first, then **the larger pred+succ count**, then the block number.

- On main the sweep's Err edge is a block that only holds `%566 = inttoptr i64 %_386.sroa.19.3 to ptr; br bb64` (bb81: in
  MIR, 2 preds + 1 succ = 3). The sweep's merged Result payload is `i64`, because the Ok amounts and the Err pointers join
  in one phi, and the `.map(|()|amount)` passthrough of the native arm keeps an unknown-tag Ok path.
- The post-sweep Err join `bb62` (sharing CPI, pool CPI, and event/emit_cpi Errs: 3 preds + 1 succ = 4) ends the
  `signer_seeds` temporaries' lifetimes. It is visited first, and its sharing-CPI copy (`%1656 = COPY %357` in the call
  block at 64304r, before the tag test) joins the payload class.
- When bb81's `%1658 = COPY %1629` is reached, `swept` (live in the CPI call block on the Ok path) interferes at 64304r
  (`interference at %1658:29@64304r`). Swept stays separate, gets spilled, and r9 is not held across the clone run.

In 7fb9 the sweep's Ok paths are jump-threaded past the tag test. The remaining payload phi is `ptr`, the Err edge needs no
block, and its copy sits in the sweep-exit block (3 preds + 2 succs = 5). So swept joins first, and the post-sweep join
(`bb66`, 4) is left as its own class (`%1666`, copied at the exit).

`tools/coal.py <m.ll>` prints all of this for any module: payload class, whether swept is in it, its register, the
`%0` split candidate, and clonefeat.

## 2. IR and source probes of the mechanism

All rows are on 16c10e6. Rows marked "IR" are llc-oracle edits of the post-opt module (`edits/`). Rows marked "src" are
source genes measured with the raw-IR opt oracle (capture + `rx.py`, tokens equal to a build).

| probe | swept in payload | payload reg | `%0` split | cf | bytes | ratio |
| --- | --- | --- | --- | --- | ---: | ---: |
| main | no | r8 | r6 / 96 bundles | 2/6 | 27,400 | 0.62043 |
| 7fb9a5e3e7a2 reconstructed (1b1f711 + 6 hc genes, hash dad70e97) | yes | r9 | r9 / 57 | **6/2** | 27,400 | 0.40084 |
| IR `i_nobb81`: Err edge straight from sweep.exit (inttoptr hoisted) | yes | r7 | r6 / 82 | 2/6 | 27,432 | 0.48024 |
| IR `i_j3`: post-sweep Err join cut to 2 preds (non-empty pre-join) | yes | r7 | r6 / 82 | 2/6 | 27,504 | 0.51607 |
| IR `i_ev64`: event/emit_cpi Errs go to the final join, not bb62 | yes | r7 | r6 / 82 | 2/6 | 27,456 | 0.54317 |
| IR `i_j3` + bw 2000:1 on the inlined to_string `fmt` branch (line 296) | yes | r7 | **r7 / 57** | **6/2** | 27,456 | 0.58477 |
| src `nat_q`: `transfer_native(..)?;Ok(amount)` (no passthrough) | yes | r7 | r6 / 81 | 2/6 | 27,368 | 0.43975 |
| src `nat_flat`: `if amount>0{..?;transfer_native(..)?;}Ok(amount)` | yes | r7 | r6 / 81 | 2/6 | 27,328 | 0.44038 |
| src `ss_scope`: `signer_seeds` temporaries in a block that ends after the pool CPI | yes | r7 | r6 / 82 | 2/6 | 27,456 | 0.53569 |

So the mechanism has two parts, and the source can reach only the first today:
1. `swept` must coalesce into the Err-payload class. The sweep-result shape (`nat_q`) or the `signer_seeds` scope
   (`ss_scope`) does this from source. Both change the CFG, and MachineBlockPlacement re-lays the post-sweep chunk
   (-0.08 to -0.18).
2. The `%0` region split must pick the register that class holds across the clone run. With the coalesced class on r7,
   the split still picks r6. The only flip found (`i_j3` + bw296) needs a nonsensical block frequency.

`tools/bwscan.py` (branch weights 1:2000 / 2000:1 on all 147 condbrs, clonefeat objective) on main gives 6/2 at 5 points
and 5/3 at 13. The 5/3 points are the Rc `inc_strong` overflow traps. Every one of them carries a large layout or size change
(best 0.55722 @ 27,256, `sharing_update==None` hot). On the coalesced `i_j3` module it gives 6 points at 6/2.

### Coalesced source state plus 6/2-build genes (main 52c0b08, raw-IR oracle, `tools/coal.py`)

`ss_scope` brings `swept` into the payload class. Each 6/2-build gene was then added on top to look for the second part.

| ss_scope + | bytes | ratio | payload reg | `%0` split | cf |
| --- | ---: | ---: | --- | --- | --- |
| (none) | 27,456 | 0.53509 | r7 | r6 / 82 | 2/6 |
| holder_unwrap | 27,264 | 0.56135 | **r9** (the original's) | r7 / 87 | 2/6 |
| su_iflet | 27,464 | 0.57092 | r7 | r6 / 82 | 2/6 |
| n306_okorelse / fee_unwrap_or / curve_edit_first / shared_flat / n298_iflet | 27,448-27,568 | 0.534-0.535 | r7 | r6 / 82 | 2/6 |
| shared_owner_first | 27,464 | 0.50209 | r7 | r6 / 80 | 2/6 |
| v_holder_unwrap | 27,568 | 0.36464 | r7 | r6 / 80 | 2/6 |

`skip join before the tag test` (IR `i_skipjoin`, the w13a36 e11 form) alone does **not** coalesce swept
(payload r8, 22 loads; 0.52502 @ 27,384). The skip predecessor does not change the Err-edge block's pred count.

`tools/bwscan.py` was then run on the coalesced states:
- `ss_scope`: 6/2 at bw296_hi (0.54363).
- `ss_scope`+holder_unwrap: 6/2 at bw2920_lo (sharing arm cold) **0.56122** and bw2960_hi 0.56046, against 0.56135
  without them. Once swept is coalesced and its class sits on r9, the clone-run flip costs nothing, but it gains nothing
  either, because the frame and spill slots stay where they were.

So the original's 6/2 clone run comes with the original's frame and its swept/payload coalescing. Neither is a
stand-alone lever at 27,400 B on this main.

## 3. Gene screen on 16c10e6 (measure.sh, zero normalized losses everywhere)

The genes of all six 6/2 builds that still apply to main. su_iflet is the reverse direction, because main already has
`match sharing_update`. validate_keys_ref and sharing_key_once are already in main in spirit (`&sk`).

| trial | bytes | ratio | clonefeat | segstat both 0x4200 / 0x4400 |
| --- | ---: | ---: | --- | --- |
| main | 27,400 | 0.62043 | 2/6 | 22 / 25 |
| n298_iflet | 27,400 | 0.62043 | 2/6 | byte-identical |
| curve_edit_first | 27,400 | 0.61983 | 2/6 | 22 / 25 |
| v_holder_unwrap (`hopt.unwrap_or(false)` in validate) | 27,400 | 0.49760 | 3/5 | 25 / 26 |
| shared_owner_first | 27,384 | 0.60773 | 3/5 | 25 / 26 |
| shared_flat | 27,392 | 0.62022 | 2/6 | 22 / 25 |
| su_iflet | 27,392 | 0.62022 | 2/6 | 22 / 25 |
| fee_unwrap_or | 27,408 | 0.61824 | 2/6 | 22 / 25 |
| n306_okorelse | 27,328 | 0.61857 | 2/6 | 22 / 25 |
| holder_unwrap (execute) | 27,168 | 0.61592 | 2/6 | 22 / 25 |
| ql_before_shared | 27,216 | 0.59221 | 2/6 | 40 / 11 |
| sko (`a.sharing_config.key` passed directly) | 27,320 | 0.53855 | 2/6 | 23 / 24 |
| shared_bitand | 27,312 | 0.45941 | 2/6 | 40 / 11 |
| full 7fb9 set (n298, sko, n306, fee, cef) | 27,400 | 0.54554 | 2/6 | 23 / 24 |
| 7fb9 set without sko | 27,336 | 0.61668 | 2/6 | 22 / 25 |
| shared_owner_first + {su_iflet, fee_unwrap_or, curve_edit_first} | 27,376-27,392 | 0.606-0.607 | 3/5 | 25 / 26 |
| shared_owner_first + n306 / holder_unwrap | 27,304 / 27,168 | 0.59574 / 0.61501 | 2/6 | |
| v_holder_unwrap + {shared_owner_first, fee_unwrap_or, curve_edit_first} | 27,400-27,408 | 0.496-0.497 | 3/5 | 25 / 26 |
| v_holder_unwrap + holder_unwrap / n306 | 27,256 / 27,416 | 0.50946 / 0.50674 | 2/6 | |

No gene and no pair reaches 6/2. The 3/5 ones restore one pump_fees reload. None gains at 27,400 B, so no size
compensation was worth running.

## 4. Bounds

`tools/bound.py` (w13a36) on the main 16c10e6 build, orig range 0x3e00-0x4a00 (the clone runs):
registers fixed **0.63002** (+0.009), registers and frame fixed **0.66177** (+0.041). For 0x4100-0x4800 the bounds are 0.62612 / 0.6393.
The original's 6/2 shape is worth at most about +0.01 in registers. Most of the region's gap is the frame (spill slots, the
flag spills at 0xa40.. against 0x9e8..). The spill slots follow from the same allocation: one high-weight pointer interval
in a register pushes the first clone's key/lamports/data/rent_epoch to the stack.

## 5. Next ideas

1. Get swept coalesced without the layout change. Keep the CFG of main, but make the sweep's Err-edge copy block
   more connected, or the post-sweep join less connected. For example, put a second Err source in the sweep Err edge
   block, or make the sweep payload phi `ptr`-typed with the `.map` passthrough kept, e.g. by passing through a
   `Result<u64>` built by a non-inlined helper. Check each candidate with `tools/coal.py` before building.
2. Once swept is coalesced, screen genes or frequencies on the coalesced module with `tools/bwscan.py` and `tools/coal.py`
   for a payload register equal to the `%0` split register (r9 in the original).
3. The original's sweep exit loads the holder phi `[0x950]` and skip flag `[0x8f8]` before the tag test (orig 0x26660).
   So the skip path is a predecessor of the tag-test block, which the transpose form gives before JumpThreading threads it.
   A sweep exit that is too large to thread (more than 6 instructions) would keep that predecessor and raise its pred
   count, which is the same lever as idea 1.
