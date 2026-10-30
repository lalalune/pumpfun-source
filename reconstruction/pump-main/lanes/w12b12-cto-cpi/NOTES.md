# admin_cto StackColoring trace follow-up

Target: `0x22a10 admin_cto::execute`, 27,400 bytes. This extends the already
retained [frame-oracle packet](../w12a02-cto-iroracle/NOTES.md); it does not add
a source candidate or a matched window.

### Gain: pool-authority signer seeds as one nested literal (+0.0009 at 27,400 B, 0 losses)

```rust
// before
let pb=[ctx.bumps.pool_authority];let poolseeds:&[&[u8]]=&[b"pool-authority",mint.as_ref(),&pb];let signer_seeds:&[&[&[u8]]]=&[poolseeds];
// after
let signer_seeds:&[&[&[u8]]]=&[&[b"pool-authority",mint.as_ref(),&[ctx.bumps.pool_authority]]];
```

| metric | main 70f2704 | this change |
| --- | ---: | ---: |
| admin_cto ratio | 0.45147 | **0.45237** |
| admin_cto slots_diff | 3,308 | 3,308 |
| admin_cto bytes | 27,400 | 27,400 |
| normalized / raw | 1034 / 1034 | 1034 / 1034 |
| losses / raw losses | | 0 / 0 |
| admin_cto runtime differential | | 363 cases, 0 mismatches |
| unstripped sha256 | | 9a06045fc5ac1ac7… |

Mechanism: the seed stores before the sharing CPI now follow the original's order (`0x26680..0x26708` in the
original). The bump load comes first, then the `&bump`, `&mint` and `"pool-authority"` pointer stores, then the bump byte
store, then the signer-slice pointer, and last the lengths 1, 0x20, 0xe and 3. With separate `pb`/`poolseeds` locals,
the bump byte was stored first and the signer slice after the lengths. Only the -16 B slot shift from
the emit signer slice remains in this block. w10r1-admincto-cpi measured the same form (v2) on e61baa9
(+0.0009, same size) but never landed it.


## Round 2 (main b5975fa, after #2749 k4size): admin_cto 0.45147, 3,308 slots, 27,400 B

PR #2776 (notes) was merged. This round continues on `swarm/w12b12-cto-cpi-2`.

### StackColoring trace tool: `tools/scmerge.py` (about 5 s, no build slot)

`scmerge.py --ll module.ll --sym admin_cto7execute --llvm-bin /path/to/debug-llvm --out NEW_DIRECTORY [--edit e.py] --slot NAME` extracts the function with
the debug build's `llvm-extract` and runs the debug `llc` with `-debug-only=stack-coloring`. It prints every
StackColoring group (representative, size, members) and where each `--slot` ended up. The extracted
module compiles to the same bytes as the full module (27,400 B, identical disassembly).

What it shows for the emit signer slice `%_117.i74` (#41) on main 20a1ae9 IR:
- Every StackColoring group of 16 B or more has exactly one member that is live at the slice's start.
  That member is a sibling from the same `emit_cpi!`/event: `ix.i` (#22), `e.i` (#37), `_114.i` (#15),
  `_94.i` (#46), `authority_info.i` (#49), `_120.i` (#40), `_110.i` (#43), `ix_data.i` (#47),
  `inner_data.i` (#48), `val.sroa.6.i` (#54). The other two groups are `holder_key` and `mint`, which
  live across the wallet. So the slice has no host and becomes its own representative at fi41. It
  then absorbs validate's 7 B `target.i.sroa.0`.
- Growing the target pieces to 24 B, as in the original's 8/24 split, fills the existing 24 B groups but adds no
  new host. validate's tail goes to `ix_data.i` (#47), the `?` ControlFlow tail `_37.sroa.11` to
  `inner_data.i` (#48), and execute's `target.sroa.8` to `val.sroa.6.i` (#54). All three are absorbed
  before the 16 B slice is considered (size order), so the slice stays at fi41 (ratio unchanged).
- The original code shows one more 24 B tail copy, at T 0x680. It is written at the validation join and read just
  before `prepare_bonding_curve`. One hypothesis is that this fourth piece provides a compatible representative
  for the slice; the original IR/lifetime markers are unavailable. An IR emulation (`tools/ired/x6.py`: a fourth 24 B `t24` between
  `target.sroa.8` and `target1`) did not reproduce it. The copy through `t24` was store-forwarded away in the DAG,
  which left an EMPTY interval. The original's T24 survives codegen, so its accesses are not
  forwardable within one block.

### CPI-form trials on main b5975fa

| variant | change | bytes | ratio | losses |
| --- | --- | ---: | ---: | --- |
| m2_shvalt | sharing CPI `val` built from the validated target (`Some(Some(t))`, t = target before the `st.creator` override) instead of `Some(new)` | 27,568 | 0.42736 | size |

## Round 3 (main 17f9dc11d and later)

PR #2808 (the nested pool-authority signer seeds) was merged into main as `17f9dc11d` by the repository
owner's merge. The `land.py 2808` run that was waiting for the landing lock then returned
`{"merged": false, "reason": "PR is MERGED"}`. Main now carries both #2792 (k4size-2, `can_edit` after the fee store)
and this change. Each was measured alone; the combination is checked by the post-merge build below.

Sweep `creator-vault` signer seeds in the same nested form (measure.sh, on 70f2704 + #2792 + nested pool seeds):

| variant | change | bytes | ratio |
| --- | --- | ---: | ---: |
| m3_sweepseeds | `let vaultseeds:&[&[&[u8]];1]=&[&[b"creator-vault",old.as_ref(),&[ctx.bumps.creator_vault]]];`, passed directly to both transfers | 27,352 | 0.37541 |
| m3_sweepseeds3 | the same with the `bump` array local kept (`let bump=[..];let old=..;`) | 27,360 | 0.37266 |

| m3_sweepseeds4 | `let old=..;let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&[ctx.bumps.creator_vault]];` (bump inline, no `bump` local; `&[vaultseeds]` kept at both calls) | **27,392** | **0.45423** |
| m3_ss4bumpvar | sweepseeds4 with a scalar `let bump=ctx.bumps.creator_vault;` | 27,392 | 0.45423 (same code) |
| m3_ss4vsig | sweepseeds4 + `let vsigner:&[&[&[u8]];1]=&[vaultseeds];` hoisted once | 27,352 | 0.37481 |

Post-merge check of main 17f9dc11d (#2792 + #2808), measure.sh against `$BASE` ab83c4c66 (#2792 only, 0.45177):
admin_cto **0.45267**, 3,308 slots, 27,400 B, 1034/1034, 0/0 losses, differential 363/0 mismatches.

`m3_sweepseeds4` is the best measurement of this lane: 0.45423 (+0.0016 over main), but at 27,392 B, 8 B short.
It undoes the 8 B that k4size's `bump`-before-`old` (l1) added, which on k4 cost 0.00156. Now the bump byte is stored after the
pointer stores, as in the original (`0x24a70 ldxdw r1,[r10-0x910]; 0x24a78 stxb [r10-0x4d0],r1`). The missing 8 B
are the original's bump reload from its spill slot; ours keeps the bump in r7. Landing it needs a +8 B knob
that costs less than 0.0016. The CPI-form knobs tried on top of it are listed below.

The full nested forms are rejected. The original builds the sweep's `[seeds]` slice once (`0x24a18 stxdw [r10-0x488]`,
`0x24a80 stdw [r10-0x480],0x3`) and stores the bump byte after the pointers, as it does for the pool seeds.
In the sweep, though, the nested form shrinks the code by 40-48 B and loses about 0.08 ratio. The sweep keeps
its let-bound `vaultseeds`. The k4 `bump`-before-`old` gene is in main.

## Review boundary

The trace helper was rerun on the cached 20a1ae9 candidate IR. It reports
`_117.i74` as the 16-byte representative containing `target.i.sroa.0`; it does
not establish how the original compiler allocated its stack. The repaired
helper follows transitive merge groups, rejects missing diagnostics or unknown
selected slots, snapshots its IR input and requires a fresh output directory.
Only this parameterized helper is retained. Private source/IR mutation drivers
are omitted. Historical what-if results are not emitted-source equivalence.
