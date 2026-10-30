# Swap curve borrow timing

At upstream `77c67c4e`, `swap_hop` remains unmatched at original window
`0x5b3b0`. Passing the already-dereferenced curve into an always-inlined
helper before cloning the fee-config AccountInfo improves its generated code.
The helper reads the fee-config length, then calls `buy_fee_market_cap`,
preserving the original operation order and propagating the same errors.

| Measurement | Fresh main | This change |
| --- | ---: | ---: |
| Target bytes | 18,584 | 18,584 |
| Differing normalized 8-byte slots | 1,017 | 874 |
| Instruction similarity | 0.92654 | 0.96371 |
| Normalized windows | 1,033 | 1,033 |
| Raw windows | 1,033 | 1,033 |
| Lost normalized/raw memberships | — | 0 / 0 |

This is partial reconstruction progress, **not a new fully matched window**.
All 108 direct calls (107 internal and one syscall) retain the original callee
multiset; physical call order still differs. The first differing instruction
moves to target offset `0x1850`.

## Mechanism and prior work

This implements the source-helper hypothesis documented in
[PR #2526](https://github.com/lalalune/pumpfun-source/pull/2526): the curve-data
pointer should be formed before the fee-config clone. That analysis traced
an unwanted re-spill and stack-slot ordering to pointer formation timing.
Here the source helper plus `#[inline(always)]` produces the improvement with
the pinned compiler. The exact compiler mechanism remains an inference.
Ordinary and `#[inline]` helpers, returning the cap Result separately, and
returning the curve reference were also measured and rejected (see ledger).

This builds on the same-file fees/reserves restructuring in
[PR #2558](https://github.com/lalalune/pumpfun-source/pull/2558) and its
credited predecessor lanes. No emitted IR or ELF is modified. Source-line
coordinates, scorer and build recipe are unchanged.

## Validation and limits

`RESULTS.json` binds both source manifests and ELF hashes. A separate clean
build reproduced the candidate's stripped and unstripped hashes. Full score
snapshots preserve every baseline membership. The call-target audit reports
1,033 normalized and 1,033 bisimilar matches.

The existing `five-bytecode-followups/replay_swap.py` comparison passed all
120 synthetic single-hop cases against the original ELF. It compares errors,
curve bytes, curve quote change, user base change and buyback receipt.
Signature verification is disabled for the AMM PDA. These cases do not cover
post-complete fills, two-hop routes or Token-2022 and do not prove general
runtime equivalence.

Reproduce with the repository's pinned identity recipe, then run:

```sh
python3 reconstruction/harness/target_metric.py /path/to/unstripped.so 0x5b3b0 --sym 'multi_hop_curve::swap_hop$'
python3 reconstruction/pump-main/lanes/callgraph-census/callid_audit.py --cand /path/to/unstripped.so
python3 reconstruction/pump-main/lanes/five-bytecode-followups/replay_swap.py --candidate /path/to/candidate.so --output /path/to/new-runtime.json
```

## PR coordination

At the pre-publication open-PR scan, none shared this source file. Open
[PR #2564](https://github.com/lalalune/pumpfun-source/pull/2564) addresses the
other remaining Pump window, Admin CTO, in a different file. This is related
scope, not a confirmed conflict or dependency; its unmerged source was not
integration-tested. Merged #2526 and #2558 are credited above.

Attribution: OpenAI / GPT-6.1 Sol High (operator-reported).
