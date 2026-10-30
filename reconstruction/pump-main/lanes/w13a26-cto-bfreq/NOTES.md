# w13a26-cto-bfreq: branch-frequency sweep of `admin_cto::execute` (0x22a10)

Target `0x22a10 admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: sweep branch weights on every conditional branch of execute with an `llc` oracle, list the edits that raise
the ratio at 27,400 B, then reproduce the winners with source constructs that rustc 1.79 / LLVM 18 actually turn into
branch probabilities. Result: **no landable source change**. The weight winners need probabilities that only cold
calls, `unreachable` paths or `llvm.expect` produce, and the winners move with every main. Ledger keys
`0x22a10-w13-*-bfreq-*-v1`.

## Oracle (`tools/`)

| tool | what it does |
| --- | --- |
| `cv.sh <name> <edits.py> <slot>` | crate copy + exact source edits, then a raw-IR capture (one build slot; `capraw.py` from w13a01), `opt -O3`, and extraction of execute (`internalize,globaldce`) to `ir/<name>.ex.ll`. It prints the llc ratio, which equals `measure.sh`'s ratio (checked on bf9a05d 0.55872, 6ac6f9b 0.56291, d81d0f5 0.571 and w13a21's first candidate 0.56741). About 80-100 s. |
| `bwx.py run <ex.ll> SPEC` | llc on the extracted module (0.3 s) with `bw:BLOCK:T:F` (branch_weights), `inv:BLOCK` (swap successors) or `strip:BLOCK` edits. Scores exact masked 8-byte tokens like `rx.py`. |
| `bwx.py sweep <ex.ll> BASE OUT.jsonl -w 1:2000,2000:1,...` | every conditional br of execute times every weight in `-w`, 6 in parallel (147 brs x 7 weights in about 2 min). |
| `bwx.py brs`, `bwx.py emit` | list the branch blocks; write an edited module. |
| `bwgreedy.py <ex.ll> <sweep.jsonl> <out>` | size-pinned greedy over single-edit winners. |
| `objfn.py` | disassembly of execute from an object (from w13a17). |

zsh caution: `llc $F` with `F="-O3 ..."` does not word-split in zsh, so llc runs at -O2 defaults and execute comes out
at 28,560 B. Use `${=F}` or a bash script.

## Sweep results, by main

The landscape changes completely with each landing:

| main (ratio) | best single bw edit at 27,400 B | gain | minimum weight that gives it |
| --- | --- | ---: | --- |
| bf9a05d (0.55872) | `bb82` 2000:1: sharing CPI gate `tag != 2`, Some arm hot | +0.0048 | 2:1 or 20:12 (3:2 gives nothing) |
| 6ac6f9b (0.56291) | `bb7` 2000:1: `global_quote` `quote == default` memcmp taken | +0.0084 | 8:1 (4:1 gives nothing) |
| d81d0f5 (0.571) | `Rc::inc_strong` trap test inside the sharing-CPI manual AccountInfo clones, 1:1 | +0.0039 | (std code) |
| d81d0f5 (0.571) | `bb27.i64` 1:16 / 1:2000: wallet `collect(..)?` Err edge cold | +0.0009 | 8:1 (1:2..1:4 and 12:20 give nothing) |

- On d81d0f5, bb82 (any weight) and bb7 no longer gain. w13a01's recipe steps (`bw:start:1:2000`, `bw:bb7.i:2000:1`)
  already stopped gaining on bf9a05d (0.55842, 0.39401).
- Successor inversion (`inv:`) of every branch gives nothing at 27,400 B (bf9a05d). llc's layout and allocation follow
  BPI, not IR successor order, so arm order or negation alone cannot reproduce a bw gain.
- Weight classes that source can express, on d81d0f5 (`sweep-d81d0f5.tsv` lists every edit that changes the window):

| class | source construct | weight | single gains at 27,400 B |
| --- | --- | --- | --- |
| zero/pointer heuristic added | bool test read from memory (`icmp ne i8 x,0`), `Option<&T>` gate | 20:12 / 12:20 | bb32 (sweep gate), bb65.i96 (`amount==0`), bb9.i: each +0.0003 |
| zero heuristic removed | and-1 / i1 test | 1:1 | bb63.i (`amm_frozen`) +0.0003 |
| 3-way switch | `Option<bool>` 3-arm match | 2:1 | none (bb27.i64 needs 8:1) |
| cold successor | `#[cold]` call on the path | 16:1 | bb27.i64 +0.0009, but a non-inlined cold call adds a call (154+3 must hold) |

  None of the +0.0003 singles stacks: greedy over all of them stops after bb27.i64.

## Mechanisms behind the two large winners (both are proxies, not the original's BPI)

- **bb82, bf9a05d**: the original's gate is the same `and64 r1,0xff; jne r1,0x2,+1; ja` tag test as ours. In llc BPI
  `icmp ne i8 tag, 2` has no heuristic, so the original was 50/50 too. The 2:1 weight only reweights the spill slots of
  the sharing-CPI AccountInfo clone run: they move 8 B, from -0x998 to -0x990 (orig -0x970), and +16 tokens follow.
- **bb7, 6ac6f9b**: the original has the same three memcmp calls (default, native mint, whitelist at +0x3a8). In both
  builds BPI applies the memcmp libcall heuristic to `memcmp == 0` (equal is unlikely). The 8:1 weight keeps a
  shared constant-1 / `cashback` phi in r4, materialised per path, instead of spilling it after the first memcmp
  (`mov64 r1,1; stxdw [r10-0x8f8]`). The frame shrinks by 8 B: args spill at -0x908/-0x928, main -0x910/-0x930,
  orig -0x928/-0x938.
- **Rc trap 1:1, d81d0f5**: halving the frequency of the second half of the sharing-CPI clone run (after w13a21's
  manual AccountInfo literals) is again a spill-weight effect inside that arm. No source construct halves the frequency
  of half an arm.

So on this target, branch frequency moves spill weights and stack-slot order (StackSlotColoring and greedy split
costs). The original's own BPI was the default heuristics on the same tests. A lane that wants these gains has to
change the live ranges themselves, not the probabilities.

## Source trials (bf9a05d, raw-IR capture oracle = identity build)

| trial | change | bytes | ratio |
| --- | --- | ---: | ---: |
| s1ptr | sharing gate on `Option<&Option<Pubkey>>` (`Some(&None)`, `Some(&args.0)`, `*val`): pointer heuristic 20:12 | 27,272 | 0.49707 |
| s2shared | `if shared{let val=sharing_update.unwrap_or(None);..}` | 27,408 | 0.52748 |
| s3none1st | `match sharing_update{None=>{}Some(val)=>..}` | 27,400 | byte-identical |
| s4ifsome | `if sharing_update.is_some(){let val=sharing_update.unwrap_or(None);..}` | 27,392 | 0.55131 |

## Why the large weights are not reachable from source on this toolchain

- rustc 1.79 emits `llvm.expect` only for MIR `Assert` terminators (overflow checks, bounds checks). Those add a panic
  edge, and none survives in execute (the whole module keeps 2 `branch_weights` after `opt -O3`).
- JumpThreading writes branch weights only on blocks that already carry them, so it cannot create them here.
- `core::intrinsics::likely/unlikely` are unstable and do not reach LLVM (y1-cto-llvm).
- LLVM 18 BPI without metadata knows only these heuristics:
  - `unreachable` / noreturn successors;
  - `cold` calls, which weigh 16:1 against the successor;
  - pointer and zero (libcall) heuristics, 20:12;
  - loops;
  - switches, uniform per case.

  The bb7 and bb27.i64 winners need at least 8:1 and the bb82 winner needs a heuristic on a `!= 2` compare. Only the
  cold-call route reaches 8:1, and on these paths it adds a call.
- `#[cold]` functions in the module: `RawVec::reserve::do_reserve_and_handle`, `panic_fmt`, `unwrap_failed`,
  `handle_error`, `handle_alloc_error`. None lies on a path a bw winner needs.
