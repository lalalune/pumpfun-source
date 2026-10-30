# w7r1-execute-hillclimb-cv2: create_v2::execute (0x1e7c0) mutation hill-climb

This is lane `w7r1-execute-hillclimb` for target 0x1e7c0. It got the `-cv2` suffix because a
second agent was already using the plain `w7r1-execute-hillclimb` name, worktree and cache dir
for `sweep::execute` (0x72810). Builds and outputs are in
`~/.cache/pumpfun-reconstruction/lanes/w7r1-execute-hillclimb-cv2/`.

## Result

Analysis only. This branch has no source change. No mutation beat the best open PR.

| Build | Bytes | Ratio | Official normalized / raw | Losses | unstripped sha256 |
| --- | ---: | ---: | --- | --- | --- |
| origin/main 2b85821 | 15,584 | 0.96854 | 1027 / 276 | | ec660de7 |
| combo: `let fee=if..else` + creator store after tts (same as #2293) | 15,576 | 0.98763 | 1027 / 276 | 0 / 0 | 949a2dad |
| #2297 head b951d46 (w7r1-execute-frame), hill-climb base | 15,576 | 0.98870 | 1027 / 276 | 0 / 0 | 030d0d70 |
| best of 166 mutations on #2297 / combo | | no improvement | | | |

## Hill-climb

The harness is in `scripts/`. `muts.py` is the mutation catalog: about 150 named spelling
mutations, each an exact-text replacement that keeps the line count, plus generated families.
`batch.py` builds them two at a time through `fastbuild.py`, `trial.py` measures each one with
`target_metric.py`, and `rec.py` records every trial in the ledger. `maskcmp.py` compares a
build with `r10` offsets masked, which separates frame shifts from structural changes.

Outcomes (166 builds):

- 84 byte-identical (attractor);
- 81 worse;
- 3 compile failures;
- 0 better.

Families tried:

- **Byte-identical (attractor):**
  - Sol-return spellings: `new_from_array`, `Default::default`, let-bound, helper fn, `static`
    zero key, `Pubkey::from`, `try_from`, word-split array, tuple/source `Default`;
  - destructure forms: ref/`a`/let/mut/fields/fields reversed/`map_err`/`Into`;
  - `init_curve` attrs and `#[inline]` on `validate_metadata`/`validate_quote_mint`;
  - `unwrap_or_else`/`match`/`map_or`/`or().unwrap()`/match-all/block forms of the reserves
    default;
  - `as_ref`/`&==&`/bool-let compare forms;
  - `to_owned`/`String::clone` for the metadata clones;
  - `create_event` arg sources;
  - `&source` in `matches!`/depth;
  - `&creator`, `&*global`, init_curve arg order;
  - `repr(Rust)` struct with any of 6 field orders, and `repr(C)` in the natural order;
  - wrapper that passes the result straight through;
  - `let mint_key=Pubkey::default()` in the native branch.
- **Worse:**
  - creator store at the other 14 positions (0.9817-0.9871);
  - tuple permutations that change layout (0.78-0.82) and `repr(C)` orders (0.78-0.99);
  - `#[inline(always)]` on `validate_metadata` (0.882) or `validate_quote_mint` (0.341);
  - moving `validate_metadata` before `init_curve` (0.709);
  - inlining `Pubkey::default()` into the compare, or the ivqr load (0.8955 / 0.900);
  - `quote_mint!=sol` polarity (0.924);
  - `if let`/`is_some`/`is_none` forms (0.908);
  - explicit `match`/`if let Err` on the result (0.875, frame -0x18);
  - Sol encoded as `None` with a default in execute (0.44-0.69);
  - labeled-block single `Ok` return (0.41-0.56);
  - wrappers that destructure and re-wrap (0.7025, masked equal to base: only the frame shifts
    by +0x18);
  - `let sol` reused for the compare and the return (0.54-0.55);
  - `&quote_mint` into `init_curve` (0.50);
  - `reserves` by reference (0.98709: the reserves tag becomes an alloca store, and the
    `mov r7` order is fixed but the `-0x730` store moves).

## SROA mechanism behind the `mov r7,0`/`mov r2,0` swaps (new detail)

`opt` from the rust-dev 18.1.7 toolchain
(`~/.rustup/toolchains/solana/lib/rustlib/aarch64-apple-darwin/bin/opt`) runs
`function(sroa<modify-cfg>)` on the module dumped by `-print-before=sroa -print-module-scope`
(the dump taken after the CGSCC inliner ran on execute). This replay reproduces the validate exit
phi order exactly: 31,51,47,18,0. That is processing order 0,18,47,51,31, which is also the order
in `bb112` after JumpThreading. Edits to the pre-SROA IR are in `sroa-edits/`, and
`scripts/sroa.py` runs them in about 1 s each.

- **Fixed (`.31` promoted in offset order):**
  - both Sol `memset(_84+16, 0, 32)` replaced by `memset 8 + memset 24` (e5) or
    `store ptr null + memset 24` (e1);
  - or both deleted (e11).
- **Not fixed:**
  - only one of the two Sol sites split or deleted (e1a, e9, e10);
  - every Err store and load of the +16 slice turned into i64 (e6, e7), so it is not a
    pointer-type effect;
  - the Sol memset merged with the source-tag store into `memset 33` (e8);
  - the Ok memcpy from `mint_key` split (e4).

Rule: a memset that spans the [16,24) partition boundary delays that partition's promotion to
the second SROA round. The original therefore had no such memset on either Sol path at
execute's post-inline SROA. Every Rust zero-Pubkey spelling tried folds into a 32-byte memset
before inlining, including a `static` key (MemCpyOpt turns a memcpy from a zero constant into a
memset). The bb112 order that fixes it (`.0`, `.18` < `.31` < `.47`) gives 0.98978 on the llc
oracle.

## Remaining residual on #2297

1. The bb112 phi order above (4 slots).
2. The creator pointer is in r2 instead of r4, and the name-pointer reload sits before its use
   instead of at the top of the init_curve join (`0x20570`). This is RA. Other lanes'
   exhaustive IR scans (single moves, block moves, branch weights, branch swaps, llc greedy
   flags) found no IR-order lever.

## Next ideas (not tried here)

- A source form where each Sol path writes the quote word0 separately from the 24-byte tail
  inside execute's Result alloca at SROA time. This needs a callee whose own SROA splits a
  Result-typed local with the same Err-ptr overlap, without an extra 24 B frame slot (the
  wrappers tried keep one).
- An RA probe at MIR level (`-stop-before=greedy`, then edit vreg order or priorities) to learn
  which allocation order gives creator=r4. Diagnostic only.
