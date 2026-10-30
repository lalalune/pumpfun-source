# Swap hop is now a raw and normalized match: 1,033 → 1,034 windows

`multi_hop_curve::swap_hop` at original `0x5b3b0` now matches all **18,584 bytes**
of the captured original. The target moves from **127 differing normalized slots
to zero**, and its instruction-sequence ratio rises from **0.98907 to 1.0**.
Whole-program matches rise from **1,033 to 1,034 normalized and raw windows**,
with zero membership losses. Admin CTO remains the one unmatched window; this
is not a whole-program identity claim.

Base: `e15f7b654653e1130812096b6eda05140a41eb80`, freshly built after integrating
the latest upstream Admin CTO harvest. `RESULTS.json` binds the final source,
baseline/candidate builds, independent rebuild, full score delta and runtime report.

## Source changes and mechanism

- Express `base <= reserves` as `!(!base).overflowing_sub(!reserves).1`.
  Complementing reverses unsigned order: `!base < !reserves` exactly when
  `base > reserves`. The wrapped subtraction result is unused.
- Match the completion `Option` with `None` first; both arms return the same
  values and the preceding `Result` propagates the same errors.
- Return `(allowed, global)` from validation and pass that same `&Global` to
  `complete_fill`, retaining the reference across validation.
- Put transfer-fee calculation, checked adapter subtraction and the buy body
  under one `if buy` scope. The old code split them across correlated buy tests.
  The sell path previously computed `amount.checked_sub(amount) == Some(0)`;
  that unused zero calculation is omitted. All actual calls and errors retain
  their order, and error source-line coordinates are unchanged.

The measured search sequence was 127 → 89 → 57 → 39 → 38 → **0** slots.
The last scope change gives the original two Result branch shapes: `jeq` plus
`ja` after `post_fee_amount`, and a single `jne` after buy `get_fees`. It closes
all remaining differences without changing the function's size.

Temporary compiler-IR diagnostics helped identify these block-order effects;
**the delivered result is rebuilt solely from Rust source**. No emitted binary,
IR, scorer, compiler setting or linker input was patched for the candidate.
The private search tooling is not included in this contribution.

## Verification

- Full 1,035-window baseline and candidate censuses accompany this lane.
  There is one new normalized/raw match (`0x5b3b0`) and no losses.
- The final candidate was rebuilt in a new build directory, reproducing both
  unstripped and stripped ELF hashes. Source fingerprints and linker/toolchain
  digests are retained in `RESULTS.json`. The identity recipe uses the pinned
  v1.44 macOS compiler and matching Linux target libraries.
- All 108 direct/syscall callee signatures match the original in order.
  Call-target audit retains **1,034 bisimilar matched windows**. This is a
  diagnostic, not a whole-program equivalence proof.
- **256/256** compiled-candidate/original synthetic single-hop SOL/SPL cases
  agree on errors, non-executable account snapshots, events, inner calls and
  return data. The reserve-crossing family includes 68 successful cases and
  28 with completion events. Signature checking is disabled for the fixture's
  AMM PDA; two-hop execution and arbitrary on-chain states are not covered.

The replay copies the candidate to a private temporary file before executing,
checks captured input hashes before/after the run, binds its report to the
candidate digest, and refuses an existing output path.

Build fresh main and this branch with `reconstruction/harness/fastbuild.py` and
the pinned identity setup, then run:

```sh
python3 reconstruction/harness/score.py /path/to/candidate/unstripped.so \
  --baseline /path/to/main-score.json --json /tmp/swap-score.json
python3 reconstruction/harness/target_metric.py /path/to/candidate/unstripped.so \
  0x5b3b0 --sym 'multi_hop_curve::swap_hop$'
python3 reconstruction/pump-main/lanes/swap-reserve-predicate/replay.py \
  --candidate /path/to/candidate/candidate.so --output /tmp/swap-runtime.json.gz
```

Runtime replay uses the repository's solders 0.27.1/LiteSVM environment.

## Coordination and attribution

The open-PR changed-file scan found no other open PR changing this swap source
or evidence lane at publication preparation. Related and preceding work:

- [#2611](https://github.com/lalalune/pumpfun-source/pull/2611): merged work in
  this file establishing the 127-slot baseline; its adapter binding and final
  Option iteration are retained.
- [#2574](https://github.com/lalalune/pumpfun-source/pull/2574): merged borrow
  and Global pointer-lifetime reconstruction in this function.
- [#2576](https://github.com/lalalune/pumpfun-source/pull/2576): our closed earlier
  proposal, superseded by #2574. This contribution starts from accepted main.
- [#2642](https://github.com/lalalune/pumpfun-source/pull/2642): Admin CTO harvest
  now integrated upstream; the final baseline and candidate include it.
- [#2621](https://github.com/lalalune/pumpfun-source/pull/2621): related Admin CTO
  work in different files. No separate integration of that unmerged branch was tested.

Historical shared files or related scope are not claims of a current conflict
or unmerged dependency. Prepared as Oz-0s using Codex desktop,
OpenAI / GPT-6.1 Sol High (operator-reported).
