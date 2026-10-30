# Swap hop: reserve predicate and completion branch, 127 → 57 slots

`multi_hop_curve::swap_hop` at original `0x5b3b0` retains its original
18,584-byte size while differing normalized instruction slots fall from **127 to
57**. The instruction-sequence ratio rises from **0.98907 to 0.99563**.
This is partial reconstruction progress, not a new full-window match.
All **1,033 normalized / 1,033 raw** matched windows are preserved, with zero
membership losses or gains. Base: `319a7d10f68b9d45ac812332133a45ba9264c8a0`.

## Source change

- Express the unsigned `base <= reserves` check as
  `!reserves.overflowing_sub(base).1`. Unsigned subtraction underflows exactly
  when `reserves < base`; the wrapped difference is discarded.
- Express the completion `Option` as a `match` with `None` first. Both arms
  return the same values and the preceding `Result` still propagates errors.

The predicate alone reaches 89 differing slots. Adding the completion match
reaches 57. The combination recovers the original raw-output overflow block
placement, error-return loads, and completion Some/None block placement. It leaves
41 slots around the two early Result branches and 16 around the reserve compare
and Global argument setup. Region 1 and the last 945 instructions remain exact.
Source error-line coordinates, outlined helper signatures, compiler settings and
linker inputs are unchanged. No emitted binary, IR or scorer patch is used.

## Verification

`RESULTS.json` pins the baseline, candidate and independent rebuild source/ELF
hashes. The candidate was rebuilt in a new build directory, reproducing both
unstripped and stripped ELF hashes exactly. The pinned identity recipe uses the
v1.44 macOS compiler and matching Linux target libraries.

- Complete 1,035-window score censuses and source fingerprints accompany this lane.
- All 108 direct/syscall call signatures occur in the original order and match
  their normalized callee bodies. Call-target audit preserves 1,033 bisimilar
  matched windows; it is diagnostic, not proof of general equivalence.
- `replay.py`: **256/256** synthetic SOL/SPL single-hop cases agree on errors,
  non-executable account snapshots, events, inner calls and return data. The
  reserve-crossing family includes 68 successful cases, 28 with completion events.
  Signature checking is disabled for the fixture's AMM PDA. Two-hop execution and
  arbitrary on-chain states are not covered by this replay.

The replay copies the candidate to a private temporary file before executing and
checks captured input hashes before/after the run. Its report is bound to the
candidate digest, and existing output paths are refused.

Build a fresh main and this branch with `reconstruction/harness/fastbuild.py` and
the pinned identity setup. Then run:

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

The open-PR changed-file scan found no other open PR changing
`programs/pump/src/multi_hop_curve_swap.rs` or this evidence lane.

- [#2611](https://github.com/lalalune/pumpfun-source/pull/2611): merged work in
  the same file that established the 127-slot baseline. This builds on its
  adapter-difference binding and final Option iteration.
- [#2574](https://github.com/lalalune/pumpfun-source/pull/2574): merged borrow and
  Global pointer-lifetime reconstruction in the same function.
- [#2576](https://github.com/lalalune/pumpfun-source/pull/2576): our closed earlier
  partial proposal, superseded by #2574. This PR starts from accepted main.
- [#2642](https://github.com/lalalune/pumpfun-source/pull/2642) and
  [#2621](https://github.com/lalalune/pumpfun-source/pull/2621): related work on
  Pump Main's other remaining function, Admin CTO; different source/evidence files.

Related scope or historical shared files do not imply a current conflict or an
unmerged dependency. Integration with those open branches was not tested.
Prepared as Oz-0s using Codex desktop, OpenAI / GPT-6.1 Sol High (operator-reported).
