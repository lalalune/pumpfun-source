# Count static patterns before limiting displayed examples

`deep_section_analysis.py` detects deserialization-pattern candidates across all
inferred windows, then returns at most 100 example records. Its packet summary
and README counted that limited list. For Pump, the actual producer found 1,208
candidates while the generated report said 100.

The correction adds the full count and the displayed count to Layer 4, uses the
full count in the summary, and states both in the README. The 100-example cap,
detector rules, example order/content, and inferred-size list stay unchanged.
These are heuristic candidates from observed loads, not proven structure layouts.

## Actual captured inputs

Base: `9120883a957d7d9b2cab6140f66fb5bc9e6774d5`, Python 3.12.13.

| Capture | Full detected count | Displayed examples | CLI summary before → after |
| --- | ---: | ---: | ---: |
| Pump | 1,208 | 100 | 100 → 1,208 |
| Pump AMM | 742 | 100 | 100 → 742 |
| Pump Fees | 578 | 100 | 100 → 578 |
| Mayhem | 441 | 100 | 100 → 441 |
| Donation Relay | 483 | 100 | 100 → 483 |
| Associated Token | 86 | 86 | API control |
| SPL Token | 24 | 24 | API control |
| SPL Token 2022 | 420 | 100 | API check |
| Token Metadata | 314 | 100 | API check |

`probe.py` reads all nine unchanged captured ELFs. A read-only Python profile
callback observes the actual producer's completed list before its display slice;
it changes neither instructions, intermediate rows nor the returned result.
The probe also runs the uninstrumented CLI for the five supported selected
programs and runs each generated packet verifier. Each CLI Layer 4 document
equals the corresponding API result. Thus the full CLI mismatch is checked
against actual detected candidates, not invented input rows.

`results.json` retains capture and pattern hashes. Across revisions, every
existing Layer 4 field is identical, including the displayed rows and the full
inferred-size list. All other layer files are byte-identical in the five CLI
packets. Both smaller uncapped captures preserve their full displayed counts.

Run the same probe against each checkout, choosing fresh output files:

```sh
python -B research/section-pattern-count-20261101/probe.py \
  --checkout /path/to/base-checkout --output /path/to/before.json --expect base
python -B research/section-pattern-count-20261101/probe.py \
  --checkout "$PWD" --output /path/to/after.json --expect fixed
python -B scripts/test_deep_section_pattern_count.py
```

The maintained CI invokes the new retained-capture and actual-CLI regression
suite. The probe and tests perform static analysis only: no compiler build,
model, VM, program invocation, new reconstruction score or runtime claim.

Related merged #1991 fixes per-pattern inferred extents before a 20-field display
cap; #2182 uses actual load widths; #3349 excludes frame reads. This correction
preserves those rules and addresses the aggregate count after the separate
100-pattern presentation cap. Historical packets and captures are unchanged.
