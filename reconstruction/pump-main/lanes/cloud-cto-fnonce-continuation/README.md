# Admin CTO success continuation: controlled source trials

This lane records three **negative**, full-source `FnOnce` continuation experiments for the final Pump Main `admin_cto::execute` window. It adds no production program change. The clean input is commit `304b03a82dff9db633edb48ea2e1bbe99734fadd`, whose `admin_cto.rs` blob is `c5e94190b1967ae20914625615ce362667fe16eb`. All three stages change only that source file, keep its 772 lines and the error macro locations, and build successfully with the same root compiler argv, working directory, output path, and four direct dependency rlibs. The patches, `source-manifest.json` (141 pinned source paths), and `receipt.json` make the source and build inputs reviewable.

The earlier fee-exit question and per-arm analyses are in [#3397](https://github.com/lalalune/pumpfun-source/pull/3397), [#3593](https://github.com/lalalune/pumpfun-source/pull/3593), [#3596](https://github.com/lalalune/pumpfun-source/pull/3596), and [#3617](https://github.com/lalalune/pumpfun-source/pull/3617). The contemporaneous negative work in [#3632](https://github.com/lalalune/pumpfun-source/pull/3632) and [#3633](https://github.com/lalalune/pumpfun-source/pull/3633) covers related per-arm and fee-None forms. The contribution here is the matched **full-source** continuation A/B/C evidence and the actual owned-control JumpThreading capture. It does not claim to discover per-arm threading.

## Source variants

Apply `01-clean-to-a.patch`, then `02-a-to-b.patch`, then `03-b-to-c.patch` to the pinned clean tree. Stage A moves the success continuation into `validate<T, F: FnOnce(&Pubkey) -> T>` while retaining `new: Option<Pubkey>` by value. It selects the target by reference and calls `finish(target)` only after the existing validations and fee check. Its shared-first closure returns `(target, collect_old, sharing_update, skip)`. Stage B changes **only** that closure to holder-first. Stage C changes **only** the closure root from `if holder` to `if hopt == Some(true)`; the enclosing source defines `holder` by that exact expression. The four holder/shared cases retain the same output tuple, and the original validation and error order is retained. These are compiler-shape probes, not proposed fixes.

| Input | Execute bytes | SHA-256 | Raw equal 8-byte slots / compared slots | Unmatched length |
| --- | ---: | --- | ---: | ---: |
| Clean cloud control | 27,400 | `cd1f79e5fb620c13b24f94b52586f1bd3f0fd1eafdf9c157015110ef88b6743e` | 187 / 3,425 | 0 |
| A: shared-first continuation | 27,312 | `8074378e18d3c6f87d091d942b192bc3ebbaf9fba301ef4a7c398889b4707497` | 30 / 3,414 | original tail 88 B |
| B: holder-first closure | 27,528 | `8a43c185f249c43cae79cdafe71e77a154891e39eaedcdcd57b079b12de24cb4` | 26 / 3,425 | candidate tail 128 B |
| C: captured Option root | 27,440 | `36465a3b5c9d34100231d9b6145faec22226d0d29dd9766e4bf01355d0e76c7c` | 56 / 3,425 | candidate tail 40 B |

The comparison input is only the authenticated original execute window `[0x22a10, 0x29518)`, length 27,400 B, SHA-256 `6a7659fd34097683cbfdae56187f5f73a3ecae20e52ac06a3fd25837e4137a96`. Each slot count is a raw positional equality count over the shorter function's whole 8-byte instructions. These counts are **not** completion percentages. All four functions differ from the original.

## JumpThreading observations

The exact-function filtered first pass shows that B exposes a direct holder-root branch, but its holder/fee-None predecessor remains joined with nonholder/fee-None and fee-Some at the root. A separates a nonholder/fee-None route instead. C removes B's zext/recomparison route by testing `hopt` directly, but the holder/fee-None edge still does not separate. The retained dumps establish graph topology, not the compiler's precise rejection reason or a cached LazyValueInfo edge-query result. No threshold, pass-order, or compiler change was tried.

For the **clean owned-target control**, a separate diagnostic-only root compile emitted byte-identical execute bytes and an identical unstripped ELF to the ordinary control. Before first JumpThreading, `%449` (nonholder) and `%457` (holder) each build a target as 7-byte copy, two middle 8-byte loads, and 9-byte copy. Fee-None from both branches and fee-Some success converge at `%464`; `%464` copies the 7/9-byte pieces to `%201/%202`. The Result success/error test is `%563` to `%569/%570`. At `%569`, eight 7/9-byte `memcpy` calls carry `%201/%202` through `%123/%124`, `%203/%204`, `%199/%200`, and `%205/%206` before the shared/holder tree. After first JumpThreading the success/error test is folded: `%448` and `%456` fee-None branches, plus fee-Some success `%545`, still meet at `%559`, which retains those copies and branches on shared `%241`. It does **not** separate holder/fee-None at that pass. `llvm.lifetime.*` and `llvm.experimental.noalias.scope.decl` are free in the pinned target TTI, so this report does not count them as cost-2 instructions or infer a numeric rejection cost.

The original's admitted entry split has 1/7/8/8/9-byte pieces. Its two middle 8-byte values have validation and sharing consumers, while the edge pieces' saved destinations feed sharing. Earlier [#3103](https://github.com/lalalune/pumpfun-source/pull/3103) already observed that partial reuse; it does not prove the original had an owned 33-byte entry object. Our CPS temporary early 33-byte copy was only the sharing payload. That difference is an unresolved ownership/dataflow constraint, not a reason to force a copy.

## Rebuild and limits

The experiment used the official Anza `platform-tools-linux-x86_64` v1.44 host compiler, the repository's pinned Linux v1.44 `sbpf-solana-solana` target libraries, and a one-member workspace. The release profile was `opt-level=3`, `panic=abort`, `overflow-checks=on`, `lto=false`, `codegen-units=1`, `embed-bitcode=no`. `receipt.json` gives the toolchain and direct rlib hashes plus the **display-sanitized** root argv. Equality of A/B/C's root argv, cwd, output location, and direct rlib paths and hashes was checked on the actual unsanitized receipts before preparing this report. The clean control's diagnostic emission was verified against its ordinary emission; A/B/C diagnostic-versus-ordinary parity was not separately measured.

To rebuild a stage from source, install the official v1.44 Linux SDK as described by `reconstruction/toolchain/bootstrap.py`, then use a detached clean worktree at the pin. Keep copies of these patches outside that worktree. From the worktree root, apply them in order through the stage wanted:

```sh
git apply /path/to/01-clean-to-a.patch
# For B, also apply 02-a-to-b.patch; for C, also apply 03-b-to-c.patch.
python3 reconstruction/toolchain/bootstrap.py --sdk-check full
python3 reconstruction/harness/fastbuild.py --src programs/pump --work /path/to/isolated-work --out /path/to/isolated-output --recipe identity
```

The `fastbuild.py` source path stages the one-member workspace and compiles; it does not invoke the scorer. `receipt.json` records the exact cached-artifact root compile used for the measurements, so a fresh dependency build or different paths should be treated as a new recipe until its compiler inputs are checked. This lane did not run a full scorer, execute an original binary, run runtime tests, inspect another original region, or claim whole-ELF equality. No stage is a reconstruction solution.
