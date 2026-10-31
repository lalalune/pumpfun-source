# A borrowed selected key still defers the target bytes

The last Pump Main window remains unmatched. This packet isolates a source-level
question in `admin_cto::execute`: does returning a reference to the validated
selected key remove the late creator replacement and place the target bytes
before fee validation? The result separates **choosing a reference** from
**materializing the selected target**. It is a rejected counterexample, with no
program-source change or progress-table increase in this PR.

## Actual controlled comparison

The parent is frozen source `d4219123cf0fbbefcfc7e77450efeda6684b812b`.
Its fresh cold build is run [41210896548](https://github.com/shawkkkkk/pumpfun-source/actions/runs/41210896548),
artifact `13045424986`. S5 is genuine source
`bb4a6fcaca179a8a49882a6acac3b503a1206882`, tree
`f981d5c90d5137be84c5f5d2438cf96dd3af5f17`, its sole direct child.
The source changes only five lines of `programs/pump/src/creator/admin_cto.rs`.
Its separate three-file operational child is
`e3d97702e33feb979b94bd7572ec1c9c5468bb55`, run
[41212621615](https://github.com/shawkkkkk/pumpfun-source/actions/runs/41212621615),
artifact `13047416013`.

| Observed output | D421 control | S5 borrowed key |
| --- | ---: | ---: |
| Raw-equal / normalized windows | 1,034 / 1,034 | 347 / 1,034 |
| Windows in official census | 1,035 | 1,035 |
| Raw / normalized losses against D421 | — | **687 / 0** |
| Raw / normalized gains | — | 0 / 0 |
| CTO bytes | 27,400 | 26,936 |
| Prefix through first named prepare call | 6,800 bytes | 6,976 bytes |

S5 is rejected before a token-similarity metric or VM execution. The prefix grows
while the complete function shrinks by 464 bytes; neither size change is byte
reconstruction progress. The complete root official score is retained, alongside
the native run's saved score. This reader replays their rows without rescoring.

Both cohorts retain all 263 program files, 279 tooling/CORE files and 264 staged
files. CORE rows are identical. The normal macOS 26 arm64/v1.44 recipe, full SDK
inventories, cold-target checks, registry/tool guards, 555 linker selectors,
private linker-script receipt and complete map remain recorded. Executable
controller AST differs only in the frozen source pin and description. The
maintained isolated compiler-guardian invocation is unchanged. Root performed
the secondary 39-check admissions; these are not independent-agent reviews.

## Source mechanism and premises

`SOURCE.patch` is the diagnostic, not a proposed program change. Private
validation borrows the incoming `Option<Pubkey>` and returns `Result<&Pubkey>`.
Holder success returns the holder key. Nonholder validation still rejects a
missing/zero incoming key and equality with the sharing or holder key; only then
does shared mode choose the saved creator reference. The caller immediately
copies that successful reference and preserves incoming N separately for sharing.

The public signature, source lines 314–338 containing the fee checks and both
existing volatile expressions, and everything after line 339 are unchanged. Under
valid Rust values and the unchanged read-only successful validation path, the
saved creator equals the old late account read. No signer, ownership, account or
CPI code is bypassed. This static argument justified one measurement; it is not
runtime equivalence, security acceptance or evidence of the original private ABI.

## What the native bytes establish

Offsets below are relative to the actual CTO symbol at `0x22a10`.

1. The D421 shared/nonholder suffix still transports the validated K/N first-seven
   and last-nine byte fragments through common stores at `0x1768/0x1778` and
   `0x1788/0x1798`, then overwrites those fragments from C at
   `0x1878/0x1888` and `0x18a8/0x18b8`. The selected suffix has no intervening
   direct read of those target fragments or call. Twelve direct register/FP
   queries bind the current pointers. Semantic roles reuse the credited earlier
   source/public-ABI attribution, with its alias limits.
2. In S5, C was already copied into a **state snapshot** at `0x3d0..0x408`, from
   the curve pointer rooted at `0x268`. At `0x1338/0x1340`, R7 points to that
   snapshot at FP-48; `0x1350` keeps it for shared mode, otherwise `0x1358`
   replaces it with the validated N pointer. All three N comparisons
   (`memcmp` calls `0xb78`, `0xbb8`, `0xbf8`) precede this choice. This is a
   pre-fee **pointer choice**, not a proof of the original type or lifetime.
3. The complete direct-write inventory for the distinct **selected-target slot**
   FP[-1624,-1592) consists of three four-qword blocks beginning at `0x1648`,
   `0x18a0`, and `0x1990`. The first and last follow absent-fee branches
   `0x1370` and `0xa20`; fee success reaches the middle through `0x1640`.
   R7 at the common fee path retains precisely the K/C/N pointer definitions
   `0xa30/0x1340/0x1358`. Returning a reference therefore removes the old late
   C overwrite but still defers the final target-slot copy. It does not remove
   the earlier C state snapshot.
4. Incoming N is staged separately at `0x4a8..0x4e0`, from payload offsets
   +1/+9/+17/+25 of the incoming option pointer. Its 32 bytes retain those
   definitions through the shared/nonholder copy at `0x1930..0x1968`, then
   reach separate sharing scratch and its outer copy at `0x1ac0..0x1af8`.
   This role is conditional on the tested source and valid present-N path;
   no claim is made that absent-option payload bytes are initialized.
5. Only two direct loads of the saved incoming fee tag remain in the released
   prefix: `0xa18` and `0x1360`. Borrowing the selected key did not restore the
   original three-test structure described in the earlier phase evidence.

The replayer checks 113 S5 and 12 D421 reaching relations, exact raw prefix
decodes, the complete target-write inventory, source/stage archives, all 1,035
saved score rows and original capture/body hashes. It stops at the first actual
named `prepare_bonding_curve` call and traverses no outlined helper. Indirect
alias writes and error-callee/Result representations remain outside the theorem.
In particular, the common error gate is not used to infer valid private tag bits
or to prove that every syntactic CFG edge is reachable.

## Repeatable read-only replay

The four immutable URLs, exact sizes and SHA-256 values are in `inputs.json`.
Download those data files to local paths and run from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  reconstruction/pump-main/lanes/borrowed-selection-s5-negative-20261031/verify.py \
  --repo . --native-zip /path/to/s5-borrowed-selection-raw.zip \
  --capsule /path/to/s5-borrowed-selection-admission.tar.xz \
  --control-zip /path/to/d421-current-raw.zip \
  --control-capsule /path/to/d421-current-admission.tar.xz
```

Expected: `PASS_BOUNDED_S5_BORROWED_SELECTION_NEGATIVE_REPLAY`, raw 347,
normalized 1,034, 687 raw losses, 113 candidate and 12 control queries. It performs
no network request, subprocess, compiler invocation, official score, similarity
metric, VM execution or source mutation. Retained secondary checks are inspected,
not independently rerun by this verifier.

## Material prior work and limits

The original pre-fee selected creator and distinct incoming sharing-key evidence
remains credited to [PR #3639](https://github.com/lalalune/pumpfun-source/pull/3639)
and its 05e4/434b premises. It is not reproved by choosing a reference in S5.
[PR #3483](https://github.com/lalalune/pumpfun-source/pull/3483) preserves S1–S3;
S3's owned settings carrier is a different negative mechanism. The S4 unit-return
and w13 out-parameter failures remain material. The H1 full-Option projection
counterexample is preserved in [PR #3649](https://github.com/lalalune/pumpfun-source/pull/3649).
No global novelty claim is made from a bounded search of those priors.

Upstream [PR #3666](https://github.com/lalalune/pumpfun-source/pull/3666) meanwhile
changed state-literal evaluation order and reports M2249 and 388 runtime cases.
Those remain that author's results. S5 is an explicitly frozen D421 experiment,
not a current-main candidate qualification. It receives no metric or VM after
the raw loss; no padding, binary transplant, IR edit or source-size repair follows.
These observations do not establish original Rust source, exhaustive behavior,
whole-ELF equality or a successful final window. They narrow one failed mechanism:
selecting the correct referent early does not determine where target bytes land.
