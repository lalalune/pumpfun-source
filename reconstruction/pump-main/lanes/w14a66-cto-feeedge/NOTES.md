# w14a66-cto-feeedge: a block on validate's fee-Some exit edge (E334 before it), repaid with the curve fee if-let

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w14a54-cto-feetag (#3375, section 5 idea 1), w14a49 (#3347), w14a36 (#3325) and w14a52 (#3364).
Bases: main 2e1379d (0.65728 / 3,192), then 304b03a (0.65788 / 3,223). Ledger approach `feeedge`,
keys `0x22a10-w14-{2e1379d,304b03a}-feeedge-*`.

## Result (main 304b03a)

| | ratio | slots | bytes | normalized / raw | errseq (lines 7-10) |
| --- | ---: | ---: | ---: | --- | --- |
| main 304b03a | 0.65788 | 3,223 | 27,400 | 1034 / 1034 | 330 338 410 334 |
| IR bound: empty-asm block on `bb58.i -> bb74` | 0.66447 | 3,221 | 27,400 | | 330 338 334 410 |
| vl3 alone (oracle) | 0.66437 | | 27,408 | | 330 338 334 410 |
| cu_iflet2 alone (oracle, w14a53) | 0.65828 | | 27,392 | | 330 338 410 334 |
| **vl3 + cu_iflet2 (measure.sh)** | **0.66477** | 3,230 | **27,400** | 1034 / 1034, no losses | **330 338 334 410** |

Differential: 363/363 cases, no mismatches. The result is above the empty-block IR bound.

Change (two lines, line count unchanged):
- validate, at the end of the fee-`Some` arm after the 338 range check:
  `unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};`
- curve store (line 757): `if let Some(f)=fee{curve.creator_fee_bps=f;}` (w14a53's `cu_iflet2`, -8 B).

### Why it works, and what it is not

The original has its own block on validate's fee-Some exit (orig 0x24210: `stxdw [-0x918],r4; stxdw [-0x948],r3;
mov r7,1`, then its own copy of the shared test). In ours that exit branches straight into the shared join `bb74`, so
MachineBlockPlacement chains E334 after the 410 block. Codegen can never split that edge, because BPF `analyzeBranch`
cannot analyse conditional branches (w14a54). So the block must already exist in IR, and it must hold a real instruction:
an IR `fence` survives ISel but leaves an empty MBB, which branch folding deletes.

A volatile byte load through a pointer that is already in memory (`holder_key`, `sharing`) is the cheapest IR instruction
that survives opt and llc without moving any alloca. With that block present, E334 is placed after E338 and before the
fee-Some exit, as in the original. **This load is a placeholder for the original's block contents, not original source.**
The faithful form is the per-exit copy of the join (section 2), and it should replace the load once a lane can produce it.

## 1. Edge-block sources tried (raw-IR capture + rx opt/llc oracle, eq_main verified on both bases)

On 2e1379d (main 0.65728 @27,400):

| spelling at the end of the fee-Some arm | ratio | bytes | errseq |
| --- | ---: | ---: | --- |
| `core::hint::black_box(())` | 0.58553 | 27,304 | 330 338 334 410 |
| `core::hint::black_box(f)` | 0.58518 | 27,336 | 330 338 334 410 |
| `compiler_fence(SeqCst)` | 0.44481 | 27,408 | 330 338 410 334 |
| `read_volatile(&st.max_fee)` (st alloca) | 0.57744 | 27,192 | 330 338 334 410 |
| `read_volatile(&f)` (forces an alloca) | 0.42397 | 27,392 | 330 338 334 410 |
| `read_volatile(&new ..u8)` (new gets spilled) | 0.5916 | 27,352 | 330 338 334 410 |
| `read_volatile(sharing ..u8)` / `..u64` | **0.66627** | 27,352 | 330 338 334 410 |
| `read_volatile(holder_key ..u8)` (vl3) / `..u64` (vl7) | **0.66497** | 27,408 | 330 338 334 410 |
| `read_volatile(sharing)` (whole Pubkey) | 0.66249 | 27,608 | 330 338 334 410 |

The memory-clobber barriers (`black_box`, `compiler_fence`) block optimisation across validate. On 304b03a every
`holder_key`/`sharing` load lands at 0.66437 @27,408, and only `cu_iflet2` gives the -8 B repay above.

## 2. Why the join is never threaded (the faithful mechanism)

The original's three validate exits each have their own copy of the shared test. The holder fee-None copy falls
straight into the shared&&holder arm (orig 0x23b28), the fee-Some copy re-tests holder (`jeq r8,0`), and CVP folds the
fee flag to `r7=0/0/1` per copy. That is LLVM `maybeThreadThroughTwoBasicBlocks` on the holder test `bb19` through the join `bb74`.
`bb19` has the single predecessor `bb74`, holder is known on the edges from `bb44.i` (true) and `bb45.i` (false), and
once both fee-None edges are threaded, `bb74` is left as the fee-Some exit's private successor.

It never fires in ours because of the duplication cost of `bb74` when JumpThreading runs. `getJumpThreadDuplicationCost`
counts each intrinsic call as 2, and the threshold is 6:

| IR state (execute, `-print-after=jump-threading`) | bb74 contents | cost |
| --- | --- | ---: |
| main, JT1 and JT2 | validate sret pieces → `_49` → `_405` (Try) → `_48` → `val` → `target`: 10 memcpys + ~10 lifetime markers | > 40 |
| raw-IR oracle: `?` chain collapsed to one copy (`irc1`) | 3 memcpys (7 B + 9 B hop) + 4 lifetimes; final code token-identical to main | 14 |
| raw-IR oracle: target copy sunk into the tree arms (`irs1`) | 2 validate sret memcpys + 2 lifetime.end + 1 lifetime.start + 1 dead icmp | 11 |

Other results:
- `opt -passes=jump-threading` on the final post-opt IR does thread `bb45.i` (non-holder fee-None) through `bb74`, but
  never `bb44.i`. It also threads two wallet exits: 0.64292 @27,448.
- `irs1` alone gives 0.55665 @27,368 with errseq 330 338 334 410, and no threading.
- `irs1` with `-jump-threading-threshold=8` threads only the non-holder pred: 0.43531 @27,728.

The faithful route therefore needs validate's own target alloca (the 7/9 B pieces and their lifetime markers) gone from
the inlined return block, with the target copy after the tree, at the same time. Each of those is a frame change, and
w14a52/w14a54/w13a05 priced each at -0.01 to -0.3.

## 3. Other rejected forms (2e1379d)

- `match`/`if let` instead of `?` on the validate result (4 spellings): MIR duplicates the validate call per holder arm,
  so validate is no longer inlined (22,648 B, 0.28-0.30).
- Fee None early `return Ok(target)` (let-else, `match None=>return`, `if let ..else return`): 0.540-0.543 @27,408-27,448.
- Branch weights on the 334 test (`bb54.i`) and the 338 range test (`bb58.i`), 1:2000 to 2000:1: at best equal to main.
  With 2000:1 on `bb54.i` the order becomes 330 334 338 410.

## Tools (`tools/`, experiment only; never source proposals)

- `capvar.sh`, `capraw.py`, `rx.py`: w14a54's raw-IR capture and opt/llc oracle, repointed here. `rx.py` gained `PREPASS`.
- `px.py`, `eseq.py`: post-opt llc oracle with fm, sk and errseq.
- `split1.py`: edge split, with the join name taken from `J=` (default `bb74`).
- `hoist.py`: h7, retargeted to `bb74`.
- `bw.py`: branch-weight oracle.
- `fx.py`: execute-scoped raw-IR edits.
- `dis.py`: a minimal BPF disassembler for fn.bin diffs.
- `batch.sh`: 2-worker queue.
