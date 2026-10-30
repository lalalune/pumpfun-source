## Evidence-only after merged #1436 (2026-10-29)

Merged main `3159e64` and adopted its `trade_v3.rs` verbatim. **This PR now has no production source changes.** #1436 implements the same whole-body inline sell helper and direct event CPI approach; its implementation is authoritative. #1421 and #1445 are also retained from main. The duplicate helper/source edit and merge conflict are removed.

The remaining unique contribution is independent historical research evidence: complete membership and callee comparisons, signed 117-case/351-execution runtime receipts, source/dependency manifests, replay and signature verification tools, negative controls, and residual-layout experiments. These artifacts remain bound to their stated historical revisions, especially `381dc30` and tested candidate `af00256`; they do **not** claim runtime qualification of current main or additional match gains beyond #1436. To reproduce source-bound historical verification, check out the revision identified by the corresponding manifest. Related #1426 compiler-IR work and neighboring #1420/#1419/#1400 source work remain separately credited below.

# V3 sell tail investigation

Base: `abd766d7a8c047f14af34851f64166b840c6728d`. Target: `trade::sell`, original address `0x14a8a8`.

## Current result: whole-body inlining

On base `ef400863f4e476b2eaaab0866c0b1187d8060abc`, keeping the whole sell body in an `#[inline(always)]` helper and returning it directly from the public handler reconciles the earlier conflict: direct `emit_cpi!` gives the original cleanup graph, while whole-body inlining supplies the needed temporary lifetimes. The emitter-only helper is removed. All source-coordinate lines are preserved.

| Metric | Fresh main | Candidate |
| --- | ---: | ---: |
| Target bytes (original 6032) | 6040 | 6032 |
| Diagnostic ratio | 0.98707 | 0.99728 |
| Differing normalized slots | different length | 6 / 754 |
| Calls | 47 | 47 |
| Official normalized / raw | 1020 / 188 | 1020 / 188 |
| Gained / lost memberships | — | none / none |

The six differing slots are offsets `0x30` through `0x58`: the original materializes the return-buffer pointer before the system/user account projections; the candidate materializes it after them. Every subsequent normalized slot matches. This is partial recovery, not a completed function match or runtime-equivalence claim.

All 47 ordered immediate-callee signatures (callee length plus normalized-body hash, including syscall identities) equal the original. `call-audit.json` retains both sequences. `baseline-score.json` and `candidate-score.json` retain all 1,035 memberships. Source formatting was separately rebuilt; the corrected line-neutral version is binary-identical to the working prototype. A formatting attempt that shifted source lines was rejected because it lost two existing matches.

Pinned identity build: no stack warnings. Main unstripped SHA-256 `2364778f6dbd89927a406eed95451a72890c19331e9f9252b6837d9223a837de`; candidate `a4908a99b6593bab3e561cb611d2736a6c3552df537009821a5e77135692ec6d`. Candidate stripped SHA-256 `726d56ed8ea76d20cf1466de6c3387325a6d99739e366ea1970a6174bb5f79f7`.

Validation: official full-window score, ordered call audit, 10 tooling tests and 9 retained captures. The tooling tests/capture verification are not execution of the new binary. A later VM differential run is documented below.

Rebuild using `reconstruction/harness/fastbuild.py --src programs/pump --work <cache> --out <output> --recipe identity` with the repository's pinned toolchain/cache setup. Score the fresh base and candidate with `score.py`, explicitly using the fresh base JSON as `--baseline`. Inspect `target_metric.py <candidate>/unstripped.so 0x14a8a8 --sym 'trade::sell$'`. Local cache locations were overridden for this machine; no flags, dependency versions, source wrapper or scorer matching rules were changed.

## First session outcome

Analysis only. All nine source trials were rejected and `programs/pump/src/trade_v3.rs` restored exactly. No new normalized or raw match and no contribution PR. The baseline remains 1,020/1,035 normalized and 188 raw. Its target is 6,040 bytes versus the original 6,032, with diagnostic ratio 0.98707 and 47 calls. Similarity is not correctness or acceptance.

## Reproduction and validation

Used the pinned v1.44 macOS ARM64 platform tools; all 2,785 entries in the repository SDK inventory were verified, including 25 target libraries. Isolated offline Cargo cache populated from 254 lockfile-verified crate archives. The identity build reproduced upstream unstripped SHA-256 `c130803b9a27944efbcbff751fd1226fd82d6f56b9878343d95a21faad5cc70c` and stripped SHA-256 `f1e42d32716402530cd15efb63bcc7642ff8a687802514851f59bfa4af8659e8`.

Official scorer matching logic was unchanged. Local wrappers selected the verified objdump executable; the diagnostic disassembly parser converted its decimal instruction indices to byte addresses. Every changed binary retained all baseline normalized/raw memberships; two byte-identical trials were identified by SHA-256. All nine builds succeeded without stack warnings. No runtime differential test was run for rejected candidates.

The initial control report compared against an older repository baseline and lists `0x14f4e0` as a gain. That gain is already upstream and is not attributable to this lane. All trials compare against the fresh local control.

## Experiments

| Trial | Bytes | Diagnostic ratio | Calls | Outcome |
| --- | ---: | ---: | ---: | --- |
| Outlined timestamp helper, direct emitter | 6064 | 0.69022 | 47 | Reject |
| Borrowed Result error return | 6056 | 0.97213 | 48 | Reject; extra call |
| Optional error helper | 5992 | 0.55229 | 48 | Reject; extra call |
| Direct helper success-first match | 5888 | 0.96966 | 47 | Reject; merged cleanup differs |
| Direct helper early error return | 6024 | 0.85890 | 47 | Reject; register and branch changes |
| Prepare-account projection wrapper | 6040 | 0.98707 | 47 | Byte-identical baseline |
| Named fee/clock tuple, direct emitter | 5968 | 0.77808 | 47 | Reject |
| Exhaustive inner error projection | 6040 | 0.98707 | 47 | Byte-identical baseline |
| Explicit event drop before helper return | 6024 | 0.88753 | 47 | Reject |

Exact source patches, build hashes and ledger entries accompany this note. These are rejected experiments, not changes to apply together.

## Compiler evidence

Optimized LLVM IR shows the helper's converted error tag tested against success tag 2 after CPI instruction cleanup. The external `From<ProgramError>` conversion returns an aggregate whose error discriminant range is not retained at the call boundary. The outer helper `?` therefore introduces the extra test. An exhaustive identity projection over both error variants is optimized away and cannot fix it. Direct helper returns avoid that outer test but change cleanup structure/register allocation, so eliminating the test alone is insufficient.

The prologue mismatch is present before the machine scheduler: the return-buffer address is materialized after system/user account projections. It remains in that order after machine scheduling, register allocation, post-RA scheduling and block placement. This rules out attributing that mismatch solely to a later scheduling pass. The inline account-projection wrapper optimized to the same binary.

Diagnostic `--emit=link,llvm-ir` builds altered the unstripped hash to `235c4b521326906cf1b2ccd03240430c2059379f48ee7355b3ea7035d5901b29`; their stripped hash was exactly the normal baseline. Diagnostic outputs must not be reported as normal unstripped identity builds.

## Remaining work

A source-level explanation is still needed for the original error cleanup and early return-buffer materialization together. Inspect earlier instruction selection and compare the original cleanup graph with the direct-emitter variant before attempting further rewrites. Avoid repeating these mechanisms or the earlier v3trade-coordinates trials. No binary patching, padding, unsafe assumptions or changes to the scorer/toolchain are warranted by this evidence.

## Follow-up checks after the retained improvement

Moving prepare into the public wrapper worsened the target to 6,024 bytes / 0.98569. Predeclaring its result and delaying the account borrow were each binary-identical to the retained improvement. No follow-up sell variant was retained.

The whole-body inline mechanism was also tested on `v3_buy_costs` (`0x80df8`): binary-identical, still 2,136 bytes / 0.920. Explicit `if let Err` propagation after `transfer_from_user` in `v3_execute_buy` (`0x83c00`) produced 3,448 bytes / 0.92781 with 23 calls versus the original 22, and was rejected. Both trials retained the existing 1,020 normalized / 188 raw memberships; neither found another match.

## Independent compatibility check with PR #1356

The layout-order contribution at `f98d2a7fb2e7c2295698ae2a7dd0604bdb895f47` ([PR #1356](https://github.com/lalalune/pumpfun-source/pull/1356)) reports 88 new raw matches. Its source patch was reviewed and independently built on the same base/toolchain, first alone and then with this lane's retained sell change. The layout-only build exactly reproduces its published unstripped SHA-256 `37a078b8c743a0cc95c8aefc145d5b2e497a967fe39ae7e7f084ff513d5cb432`.

Both layout-only and combined builds score **1,020 normalized / 276 raw**, with the same 88 raw gains and no losses versus fresh main. Every membership is equal between those two builds. Combined sell remains 6,032 bytes with six differing normalized slots and all 47 ordered callee signatures equal to the original. Neither build reports stack warnings. The layout-only checkout also passes 10 tooling tests and nine capture checks; no VM run was performed.

**All 88 raw gains belong to PR #1356, not this lane.** Its source changes are not included in this PR. This is independent compatibility evidence for composing the two contributions, not a duplicate source submission. `LAYOUT-COMPATIBILITY.json`, the two membership maps and combined source SHA-256 manifest retain the exact provenance and results. The local workspace was restored to this PR's own source after the check.

## Runtime qualification before review

Executed the existing 117 `sell_v3` cases from `scripts/pump_v3_configured_fee_differential.py` against the captured original, fresh-main control and this candidate: **351 locally signed executions, zero compared differences or regressions**. Each image produced 77 successful transactions and 40 expected failures (28 custom error 6024, 12 custom error 6025). All 77 successful cases emitted events.

Compared account bytes/hashes, owners and lamports (excluding the deliberately replaced Pump executable), errors, raw event payloads, inner instructions, return data and ordered logs. Only exact runtime compute-meter lines are excluded from log equality; all other logs remain ordered. Every transaction signature is verified. Compute consumption equality and exhaustive execution-path equivalence are not claimed. The suite covers native SOL and synthetic SPL Token/Token-2022 quote accounts without transfer-fee extensions, creator-fee extremes, mode flags, zero creator and reserve boundaries. The expected failures are fee validation failures, not forced event-CPI failures.

The historical fixture and replay approach are reused with attribution from [PR #1292](https://github.com/lalalune/pumpfun-source/pull/1292), pinned to `4a8336358fd5d2fd00257ef5523202222d6c8cc5`; case definitions and fixture bytes are unchanged. `replay.py` additionally fails on mismatches and compares control logs. These are new executions of this PR's candidate, not reused runtime results from that contribution. No public RPC, user wallet or live transaction is involved.

A fresh identity build from source revision `7175a27b894c6701e0f860e49ed000e3f922bb83` reproduced both tested candidate hashes exactly, without stack warnings. `runtime-manifest.json` binds fixture, receipts, runner, verifier, suite, all Rust/manifest/lock inputs, dependency images, base revision and tested binary hashes. Later commits only retain this evidence.

Reproduce in an isolated Python 3.12 environment with `solders==0.27.1`:

```sh
python -B reconstruction/pump-main/lanes/v3-sell-tail/replay.py --control CONTROL.so --candidate CANDIDATE.so --output REPORT.json.gz
python -B reconstruction/pump-main/lanes/v3-sell-tail/verify_runtime.py
```

The second command verifies retained receipts, hashes and signatures without executing programs. In-memory negative controls with an added event, an added non-meter log and invalid signature evidence were rejected. No additional normalized function match is claimed: the six-slot sell residual remains. The passing bounded runtime comparison supports marking this partial contribution ready for maintainer review.

## Bounded follow-up after runtime qualification

Checked PR #1368: no submitted reviews or inline review threads at the time of this pass. Tested four source hypotheses against revision `15486e0`, using the same pinned identity build and unchanged scorer. All were rejected:

| Trial | Target | Bytes | Diagnostic ratio | Calls | Result |
| --- | --- | ---: | ---: | ---: | --- |
| Reordered preparation adapter arguments | sell | 6032 | 0.99728 | 47 | Byte-identical retained candidate |
| Explicit preparation output reference | sell | 6040 | 0.93533 | 47 | Entry order unchanged; broader mismatch |
| Transfer success closure | v3_execute_buy | 3104 | 0.54364 | 17 | Outlined continuation; loses normalized window 0x84b78 |
| Exhaustive transfer Result match | v3_execute_buy | 3472 | 0.94811 | 22 | Worse than baseline 3456 bytes / 0.9669 |

The closure scores 1019 normalized / 188 raw; the other three retain 1020 / 188, with no gains. All builds had no stack warnings. Call counts alone do not establish callee equivalence. No rejected variant was runtime-qualified or retained. Exact source deltas and binary hashes are recorded in the focused patches and `FOCUSED-FOLLOWUP.json`; patches are relative to the retained source and must not be applied together.

Restored the previously qualified source exactly. The six-slot sell residual remains. Further buy work should inspect the transfer error join and return-buffer reload in compiler IR before proposing another source shape; these tests do not justify additional blind rewrites.

## Current-main revalidation (2026-10-29)

Merged current main `665499915f9caedcd38921d415a90f0606686398` and rebuilt both
control and candidate with the verified identity toolchain (2,785 SDK entries and
hybrid libraries checked). Both retain **1,022 normalized / 276 raw** memberships:
zero gains and zero losses. The two normalized gains versus the historical base
belong to upstream. No backend stack warnings. Dependencies were reused.

The candidate remains 6,032 bytes with only normalized slots 0x30–0x58 different
from original; all 47 ordered immediate-callee signatures equal original and control.
The unchanged retained replay executed 117 cases against all three images (351
verified signed executions), with zero behavioral or ordered non-meter-log differences.
Each image has 77 successes and 40 expected failures. Existing coverage limits apply.

`current-main-comparison.json`, `current-main-runtime.json.gz`, and
`current-main-manifest.json` retain the new memberships, receipts, binary hashes,
source hashes and toolchain verification separately from historical evidence.
Reproduce with the existing identity build instructions using the base above and
this merged source, then run `verify_current_main.py --control CONTROL/unstripped.so
--candidate CANDIDATE/unstripped.so --objdump SDK/llvm/bin/llvm-objdump --output REPORT`.
Run `replay.py --control CONTROL/candidate.so --candidate CANDIDATE/candidate.so
--output current-main-runtime.json.gz` with solders 0.27.1.
`verify_current_runtime.py` independently verifies the retained refreshed packet.

## Buy error lowering investigation

See [BUY-ERROR-PATH.md](BUY-ERROR-PATH.md) for the original/candidate return-tail comparison, compiler evidence and four additional rejected source checks. No improvement was retained. Source and prior runtime qualification remain unchanged. Exact patches and diagnostic hashes accompany the analysis in `BUY-ERROR-TRIALS.json`.

### Latest upstream follow-up

Create V2 change #1389 landed during this validation. Merged
`381dc30b35122022be7359215cb5d471fe9f778d`, then freshly rebuilt control and candidate
and repeated all static checks and 351 runtime executions. Results remain 1,022
normalized / 276 raw, zero losses, six differing sell slots, all 47 original/control
callee signatures, and zero runtime differences. Current-main JSON files and replay
receipts now bind this latest base and candidate source `af00256`.
The strengthened static verifier also rejects an original-callee mismatch or a call
count other than 47. All build logs are free of backend stack warnings.
