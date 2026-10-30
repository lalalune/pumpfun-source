# AMM sell recovery harness

The PumpSwap/AMM reconstruction has 784 of 785 physical windows raw-equal to the
deployed program. The one remaining window is the sell cashback helper
(`fn cashback` in `programs/pump-amm/src/instructions/swap/sell.rs`) at original
`0x4c750`, 9,024 bytes. This harness rebuilds the maintained AMM natively in
about 16 seconds per attempt and scores the sell window against the original,
so many source variants can be tried in parallel.

## What it reproduces

`native_build.py` uses the official macOS (aarch64) platform-tools v1.44 with the
Linux v1.44 `sbpf-solana-solana` target libraries overlaid, the qualified
layout-closure workspace transform, `-Zremap-cwd-prefix=`, `--locked --offline`
and the disclosed `ordered.ld` link script for the root crate. Cargo's
`-C metadata` hashes include the host rustc's verbose version, so the compiler
wrapper restores the Linux-host value for each target crate from
`metadata-map.json`; the link script's archive names are translated to this
host's `-C extra-filename` values. No source, object or output byte is patched.

On the maintained source this reproduces the sealed Linux container outputs
exactly: stripped `86dbc2c64e81988dead173039b61fa01ba5f68a00fbb6f6dd49f2cda0afec37f`,
symbols `7271aaf8afe13b6c8f13a6cf0e9534896a66650dda13a2aa1b32e41edd46426d`.
The sealed podman recipe (cold, empty target) reproduces the same pair.

## Layout

`AMM_SELL_SWARM` (default: the directory above this one) holds:

| Path | Contents |
| --- | --- |
| `infra/sdk-native` | macOS v1.44 platform-tools with Linux `rust/lib/rustlib/sbpf-solana-solana` |
| `infra/cargo-home` | offline registry for `programs/pump-amm/Cargo.lock` (257 packages) |
| `infra/original/deployed.so` | captured original, SHA-256 `6a7ad345…8d8ff7` |
| `baselines/pristine-ws` | workspace staged from the maintained sources by `workspace_recipe.py` |
| `baselines/warm-target` | warm dependency target cloned (APFS `cp -c`) into each new lane |
| `ATTEMPTS.jsonl`, `BEST.json`, `cache/`, `sources/` | swarm log, best result, dedupe cache, every tried sell.rs |

## Use

```sh
python3 -B try_sell.py --lane my-lane --approach my-idea --hypothesis "why" --sell my_sell.rs
python3 -B try_sell.py --lane my-lane --approach my-idea --hypothesis "why" --patch change.diff --slot 1
python3 -B sell_score.py LANE_BUILD_OUT_DIR --disasm      # aligned original/candidate listing
python3 -B attempts.py summary | best 20 | grep TEXT | approaches | seen FILE
python3 -B attempts.py note --lane L --approach A --kind dead-end --text "..."
```

`try_sell.py` restores the pristine workspace before every attempt, applies the
sell replacement or patch, forces both local crates to recompile, builds, scores
and appends one line to `ATTEMPTS.jsonl`. Identical inputs are built once per
swarm; repeats return the cached result. Exit status 3 means the sell window is
raw-equal to the original.

## Score

Image identity is reported separately from function-window matches:

- `whole_elf_equal`: exact bytes and length of the stripped `candidate.so` versus
  the captured original.
- `allocation_image_equal`: equality after zero-filling a shorter `candidate.so`
  to the capture's size. No file is modified. `allocation_padding_bytes` reports
  the added length on a match (zero for an exact match), otherwise null.
- `unstripped_elf_equal`: exact bytes and length of `symbols.so`, the retained raw
  compiler output before `llvm-objcopy --strip-all`, versus the captured original.

Reports include the three byte lengths and separate candidate/unstripped hashes.
`score_version: 2` introduced these meanings. Historical unversioned reports
used `whole_elf_equal` for the allocation comparison; they do not establish exact
file equality. The attempt cache key includes the score version so those entries
cannot be returned as current measurements. Historical logs and cached evidence
are preserved. The sell-window success criterion and exit status are unchanged.

Run the stdlib-only identity and cache regressions from the repository root:
`python -I -B scripts/amm_sell/test_sell_identity.py`. They do not compile or
execute a program, or require the native SDK.

`sell_raw_equal` is the goal. `lost_windows_normalized` must stay empty (no other
function may change). `align_distance` (instruction edit distance with branch
displacements replaced by labels) and `slot_diffs` (differing 8-byte slots) rank
partial progress; the version-2 baseline was distance 112, 709 slots. Error-macro
line numbers are encoded as immediates, so edits must keep every
`error!`/`err!`/`require!` on its current line.

Version 3 binds each branch label to the token of the instruction it reaches.
Previously, labels appeared only on the branch edges: moving a destination while
preserving its order among the other destinations produced the same token stream,
even when the branch skipped a different computation. Targets outside decoded
instruction boundaries now retain their window-relative offset. There is still
one token per instruction, so aligned disassembly retains its row correspondence.

The regression suite retargets each eligible destination in the actual 9,024-byte
captured sell window to a nearby instruction boundary while preserving destination
order. All 52 such mutations collided with the original token stream in version 2;
none collide in version 3. A separate control checks that moving a whole function
does not change its branch tokens. These are static, in-memory controls; the
captured ELF is never changed or executed. Token equality is not a proof of
semantic equivalence, and edit distance remains a diagnostic, not acceptance.

Version-3 distances must be measured afresh rather than compared numerically with
historical version-2 distances. The score-version cache key prevents reuse of the
old metric. Historical evidence and all raw image-equality criteria are preserved.

## Provisioning a new machine

1. Download platform-tools v1.44 `platform-tools-osx-aarch64.tar.bz2` and
   `platform-tools-linux-x86_64.tar.bz2` from `anza-xyz/platform-tools`; replace
   the macOS `rust/lib/rustlib/sbpf-solana-solana` with the Linux one.
2. Populate a Cargo home with `cargo fetch --locked` for `programs/pump-amm/Cargo.lock`.
3. Stage `baselines/pristine-ws` with `workspace_recipe.stage(repo, path)`; run one
   `native_build.py --lane baselines/native-a --source-root REPO --id baseline` and
   clone its `target` to `baselines/warm-target`.
4. `metadata-map.json` pairs the qualified Linux build log with a native macOS
   log; regenerate it if the host differs.
