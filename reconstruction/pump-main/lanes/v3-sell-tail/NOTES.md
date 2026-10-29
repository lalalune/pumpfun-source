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

Validation: official full-window score, ordered call audit, 10 tooling tests and 9 retained captures. The tooling tests/capture verification are not execution of the new binary. No VM differential run is claimed.

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
