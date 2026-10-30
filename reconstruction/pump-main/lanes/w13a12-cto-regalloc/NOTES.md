# Lane w13a12-cto-regalloc: register allocation in admin_cto::execute

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: register assignment and ISel temporaries. That covers the error-payload registers (orig r9/r7), which value is
computed first, and by-value copies.
Bases: main 3912c47ac (0.48772), then 085e5dffb (#2885, 0.48922), 8370e2f8a (0.49071), cb298d5c8 (0.49101) and
9eb6c0084 (0.49131, 3,280 slots).

Everything below is an experiment on IR or a measured source build. No source change is proposed yet.

## Tools (`scripts/`, text only; they use `reconstruction/harness`)

| script | what it does |
| --- | --- |
| `capture.py`, `trim.py`, `trim2.py`, `ctoracle.py` | the w12a02 llc oracle: post-opt IR capture, trimming to one function, llc plus the target_metric tokens. Re-validated on every base: tokens equal the build. |
| `regmask.py <so>` | ratio with registers masked, frame masked, or both. 8370e2f: plain 0.49071, frame-masked (abs) 0.68933, regs+frame masked 0.873. |
| `ragree.py <so>...` | aligns orig/candidate with registers and frame masked, then reports the share of structurally matched instructions whose registers agree, overall and per region. 3912c47: 0.7618. 085e5df: 0.7756. |
| `perm.py <so>` | best global permutation of r6..r9. 3912c47: +0.013 with (r6<->r9). 085e5df: the identity is best. The callee-saved assignment is not one global rename. |
| `simerr.py <so>` | renames our error-payload registers to the original's r9/r7 at the 20 `From<AnchorError>` sites: **+0.0006** only, because the sret slots sit at other frame offsets. |
| `swapscan.py <mod.ll> <out>` | llc scan that swaps every adjacent pair of independent side-effect-free instructions inside a block |
| `movescan.py <mod.ll> <out>` | llc scan that sinks every pure value to its single use block and hoists it to its single predecessor (864 edits on 8370e2f, about 5 min with 3 llc processes) |
| `regdelta.py A B [seg]` | matched tokens per original region for two builds or `fn.bin` files: where a change gains or loses |
| `side2.py`, `objdis.sh`, `tokio.py` | side-by-side view with registers and frame masked (`R` = register-only difference); disassembler for llc objects |
| `edit_sink1.py` | the IR edit behind finding 3 (`SINK=<value> ctoracle.py run mod.ll out --edit edit_sink1.py`) |
| `greedymv.py <mod.ll> <scan.jsonl> <out>` | greedy stacking of the `movescan.py` edits that changed code, size pinned |
| `clonefeat.py` | copy of w13a09's clone-run register-allocation feature (accounts-pointer spill/reg uses), reading tokens through `ctoracle.py` |

## Findings

1. **The error-payload registers are a symptom, not a lever.** Original sites load `{i64,ptr}` into r9/r7 and ours into
   r8/r6 (r6/r7 on older mains). Renaming ours gains only +0.0006 (`simerr.py`), because the sret slots are 0x20 lower in our
   frame. The slot count is 33 in both (orig 0x6d0..0x8d0, ours 0x6b0..0x8b0), so the "ISel temporaries 33 vs 32" residual is
   gone on current main. The register choice changes with distant code: #2885 (sweep skip flag) moved the accounts pointer
   from r8, as in the original, to r6, yet raised register agreement from 0.762 to 0.776.
2. **Value order inside a block does nothing.** All 226 adjacent swaps of independent pure instructions in execute's
   post-opt IR are byte-identical (main 085e5df), because SelectionDAG scheduling canonicalizes them. Source reorders of pure
   computations within one block, such as field init order of plain loads or `let` order of independent reads, cannot move
   registers. Only cross-block placement, memory/call order or the CFG can.
3. **Oracle: one late load in the sharing-CPI clone run gives +0.012 at 27,400 B.** `movescan.py` on 8370e2f: 220 of 864
   cross-block moves change code. The best at the pinned size sinks any one plain-field load of the mint `AccountInfo` clone
   in `admin_cto_sharing_config`'s accounts (owner, rent_epoch or a flag) from the clone exit block into the block that stores
   the `AdminCtoSharingConfig` struct. Result: **0.49071 -> 0.5027** (abs 0.68933 -> 0.70371, 27,400 B). The same edit on
   085e5df gives 0.48922 -> 0.5009. The gain is in orig 0x4200-0x4600:
   - the sharing-CPI clone run now reloads the accounts pointer from its spill slot before the `[accounts+0x98]` clone, as
     the original does at 0x26f08 (the w12 residual "CPI AccountInfo clone reloads the accounts pointer from a spill slot");
   - the following clones then match orig register for register.

   The original still loads that owner in place (orig 0x26d38). The edit is therefore a register-pressure proxy, one fewer
   value live out of that block, and not a literal reconstruction. The original probably gets the same relief elsewhere,
   for example from the flags it keeps in frame slots as phis of constants (orig reloads cashback/holder from `[r10-0x950]` /
   `[r10-0x958]` right after the sharing CPI; ours recomputes them in registers). Sinking all 5 loads gives 27,408 B.
   Hoists are all <= main.
   It holds on every base this lane measured (all at 27,400 B, single edit, llc oracle tokens equal to the build):

| main | main ratio | + sink one mint-clone field load | abs |
| --- | ---: | ---: | --- |
| 085e5dffb | 0.48922 | 0.5009 | 0.69053 -> 0.70491 |
| 8370e2f8a | 0.49071 | 0.5027 | 0.68933 -> 0.70371 |
| cb298d5c8 | 0.49101 | 0.5030 | 0.68993 -> 0.70431 |
| 9eb6c0084 | 0.49131 | 0.5033 | 0.68993 -> 0.70431 |

   - w13a09's `clonefeat.py` (spill/reg of accounts-pointer uses in the clone runs): 2/6 -> 3/5; the original is 6/2.
   - `swept` is still spilled (`[r10-0x948]`). The original keeps it in r9 from the sweep exit to the event store.
   - `greedymv.py` stacks the changed scan edits greedily at 27,400 B. Round 2 adds a sink of the first clone key in the
     transfer_creator_fees CPI (0.50359 on cb298d5c8), and round 3 finds nothing. **Edits that only move register pressure
     cap at about +0.0126 at the pinned size.**
   - w13a09-cto-cpiclone (#2904) already showed that no CPI spelling, IR branch weight or register pin moves the clone run.
     This sink is the first local IR edit that does, and only partly.
4. Source spellings of the sharing CPI, none landable:

| variant | ratio | bytes |
| --- | ---: | ---: |
| main 8370e2f | 0.49071 | 27,400 |
| `AsRef::<AccountInfo>::as_ref(&a.mint).clone()` / `(*a.mint).clone()` / `ctx.accounts.X` | = main (byte-identical) | 27,400 |
| mint written last in the `AdminCtoSharingConfig` literal | 0.49027 | 27,448 |
| mint after sharing_config in the literal | 0.47506 | 27,408 |
| `let program=..;let accs=..;CpiContext::new_with_signer(program,accs,..)` | 0.48861 | 27,368 |
| `let cpi=CpiContext::new_with_signer(..);admin_cto_sharing_config(cpi,val)?` | 0.47184 | 27,400 |
| `if let Some(val)=sharing_update{..}` instead of `match` | 0.49109 | 27,392 |

Ledger keys: `0x22a10-w13-085e5df-regalloc-intrablock-pure-order-scan-v1`,
`0x22a10-w13-8370e2f-regalloc-crossblock-move-scan-v1`, `0x22a10-w13-8370e2f-{mint-clone-*,sharing-*}-v1`.

## Where the remaining register differences come from (tail, orig 0x4000-0x5400)

| value | original | ours |
| --- | --- | --- |
| accounts pointer in the sharing/pool CPI clone runs | spilled, reloaded per account (`[r10-0x8d8]`) | region-split into r6 |
| `swept` | r9 from the sweep exit (`ldxdw r9,[r10-0x828]`) to the event store | spilled at the sweep exit, reloaded at the event |
| old creator fee (event field at `[r10-0x228]`) | spilled right after its load (`[r10-0x8e0]`) | in r8 to the event |
| holder / cashback after the sharing CPI | reloaded from phi-of-constants frame slots `[r10-0x958]` / `[r10-0x950]` | recomputed from the spilled `holder` arg into registers (older mains) |

The original keeps fewer values in registers through the tail. That frees a callee-saved register for `swept` and lets
the greedy allocator spill the accounts pointer everywhere instead of region-splitting it. These are consequences of
structure, such as flags kept in frame slots and the entry copy of `new` (see w13a03/w13a05/w13a08). No local source
spelling reaches them. This lane's evidence that the register-allocation angle is exhausted:
- the 226-edit intra-block scan does nothing;
- the 864-edit cross-block scan caps at +0.0126;
- 9 source spellings fail (byte-identical, size change, or worse).

## For other lanes

- An edit that only changes registers pays off only where the frame offsets already match. Perfect-frame
  (`framebound.py`) and register-agreement (`ragree.py`) numbers together show what a register fix is worth.
- Use `movescan.py` as a cheap screen on any captured candidate (~5 min, no build slot): it finds the blocks where one fewer
  live value changes allocation downstream.
