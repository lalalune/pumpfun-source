# Daybreak Blue / High — Admin CTO crash recovery and composition repair

Target: Pump Main `admin_cto::execute`, original `0x22a10`, 27,400 bytes.

Source base: `8330455eb0897493714da67aa4de6f9743d82b84` (`origin/main` fetched
2026-10-31 PDT).  All builds below used the pinned `identity` recipe, the
`sbpf-solana-solana` triple, `CARGO_BUILD_JOBS=2`, and the official scorer.

## Crash recovery

The recovery audit left every existing worktree and dirty file untouched.  The
useful prior Admin CTO work was:

- `codex/daybreak-blue-admin-cto-final-20261031`, commits `4477faa6e0` and
  `bf586592b8`, which retained the `hfcq` `CtoState` field order and its earlier
  exhaustive 24-permutation screen;
- `codex/window-d-admincto-reconstruction`, ending at `29629634c5`, which
  retained the earlier definite-assignment sweep work and rejected
  jump-threading experiments;
- `codex/daybreak-sbpf-residual-analysis`, ending at `adb7a2698b`, which
  supplied the residual/CFG analysis tools now merged upstream.

The primary checkout and several unrelated worktrees had pre-existing dirty
state.  They were not reset, cleaned, pruned, deleted, or used for builds.  The
dedicated worktree for this lane is
`/Users/muzzy5150/pumpfun-source-daybreak-admin-cto-high`.

At the start of the lane GitHub had no open Admin CTO PR.  The latest merged
source changes were W17, including #4017 and #4018.  The fresh build below
showed that the two source spellings from #4017 did not compose with #4018's
passthrough shims even though each PR improved its own tested base.

## Fresh upstream baseline

Fresh `8330455e` result:

| measurement | value |
| --- | ---: |
| instruction-token similarity | 0.68244 |
| differing instruction slots | 3,293 |
| candidate bytes | 27,400 |
| internal / relocated calls | 154 / 3 |
| normalized / raw windows | 1,034 / 1,034 |
| unstripped SHA-256 | `c2f7fc8fcc5ad67f8cc14b3ce61c7bd359dca9be389b2420f16b09743117a0f5` |
| stripped SHA-256 | `6301aa84ba59c8405b225e2b90f498a184ac2ea5efbcea9b98ab9dbdf5ff7c6f` |

This is lower than the `0.68424` merged-composition number in #4018 because
the checked-in source also contains #4017's placeholder removal and
`collection_native == false` spelling.

While this lane was being verified, upstream independently merged the same
composition repair as #4019.  The branch was rebased onto final source base
`ac37d74157c29d749a6c3f8510e8cd6408155bd0`, and the now-redundant local
composition commit was dropped.  A new cold baseline build of #4019 reproduced
unstripped SHA-256
`a950162cc7d5201c053b7a7979871132b4402989e8640bd3a631ba68a34c2482`
and similarity `0.68424`.  A new cold candidate build reproduced
`4470f55f03fa6a65a95833c68b8cca36a1c45f7538123c309b3fef30c1026767`
and similarity `0.68454`.  Therefore the final branch differs from current
upstream in only the qualified `CtoState` order plus its tests and evidence.

## Qualified source changes

### 1. Repair the W17 composition

Restore the pre-#4017 spellings on top of the passthrough shims:

- keep the `holder_key` volatile read immediately before the
  `fee_configurable` branch;
- spell the create guard as `!collection_native || coin_present`.

The pair is size-complementary and recovers #4018's reported artifact exactly:

| measurement | fresh main | repaired composition |
| --- | ---: | ---: |
| similarity | 0.68244 | **0.68424** |
| differing slots | 3,293 | 3,313 |
| candidate bytes | 27,400 | 27,400 |
| calls | 154 / 3 | 154 / 3 |
| normalized / raw losses | 0 / 0 | 0 / 0 |

The unstripped SHA-256 is
`a950162cc7d5201c053b7a7979871132b4402989e8640bd3a631ba68a34c2482`;
the stripped SHA-256 is
`5fc69980f94069abfe9c7899d7f75abf990c0d7baf754a31b71bc76dd9eebcb5`.
All 388 signed differential cases passed with zero mismatches.

### 2. Recover the prior state-layout improvement

The earlier crash-recovered `hfcq` order places the four trailing booleans as
`holder_enabled, fee_configurable, cashback, quote_locked`.  It changes
aggregate offsets and downstream register allocation without changing the
function size, CFG call census, or runtime semantics.

| measurement | repaired composition | plus `hfcq` |
| --- | ---: | ---: |
| similarity | 0.68424 | **0.68454** |
| differing slots | 3,313 | **3,312** |
| candidate bytes | 27,400 | 27,400 |
| calls | 154 / 3 | 154 / 3 |
| normalized / raw losses | 0 / 0 | 0 / 0 |

Final unstripped SHA-256:
`4470f55f03fa6a65a95833c68b8cca36a1c45f7538123c309b3fef30c1026767`.
Final stripped SHA-256:
`7251af18ef95ea907f5f6e2ec1bee80768a5671c672713bc902ed98e295a29ad`.

The 388-case signed differential again passed with zero mismatches.  The
persistent differential passed nine lifecycles and 20 distinct transactions
per image, with deterministic replay equality, no mismatch/invariant/
infrastructure failures, and all three negative controls detected.  Its report
SHA-256 is
`298ab1f8cdcfc40995a114e7e340985cc7cd61ea86ff9f9a99e5aeab9b1be7c8`.

## Rejected or tied experiments

Every experiment was restored before the next mechanism.  Full rows, artifact
hashes, and dedupe keys are in `reconstruction/pump-main/ATTEMPTS.jsonl` under
lane `daybreak-blue-admin-cto-high`.

| experiment | ratio | bytes | raw windows | decision |
| --- | ---: | ---: | ---: | --- |
| alternate `fhcq` field order | 0.68454 | 27,400 | 1,034 | metric tie; retain `hfcq` because it follows original holder-before-fee load order |
| remove only the pre-fee placeholder | 0.68434 | 27,392 | 347 | reject: 687 raw losses and size drift |
| use only `collection_native == false` | 0.68294 | 27,408 | 347 | reject: target regression, 687 raw losses, size drift |
| retune `rcincp` probability `2e-5` to `2.5e-5` | 0.68195 | 27,392 | 347 | reject: target regression, 687 raw losses, size drift |

The component-isolation results explain why the retained composition must keep
both spellings together: either half alone shifts every later raw window.

## Remaining blocker

`admin_cto::execute` is still unmatched.  The final body has the correct size
and call census, but 3,312 positional slots differ.  Existing CFG, residual,
IR, and W17 screens continue to identify register assignment, stack colouring,
and source-level lifetime/inlining boundaries as the dominant residual.  The
PDA-first source order remains structurally closer before register allocation
but still enters a substantially worse greedy-RA basin; the exhausted field
permutations and isolated W17 stitch components should not be repeated.
