# Whole-ELF relocation totals in the current analyzer

This is a maintained-CLI follow-up to
[PR #1091](https://github.com/lalalune/pumpfun-source/pull/1091), originally
contributed by [miracle2044](https://github.com/miracle2044). It is not an original
discovery. That PR supplied a separate reviewed-source adapter under
`research/program-relocation-totals/`; it did not change the root analyzer.
The cleanup merge `fce9f28dd1cc3257d65b3c20afe60acfa8955545` removed that adapter.
`history.json` binds its prior presence and current absence to Git objects.

The maintained `scripts/analyze_program.py` still labeled the sum of relocations
in code windows as `total_relocations` and “Total relocations.” Real data-section
entries were absent from that total. Its generated README describes
`summary.json` as program-level statistics. Later publication, performance and
help changes continued to maintain this CLI without integrating #1091's counts.

This change integrates the accepted distinction directly into the current CLI:
the full reader inventory is `total_relocations`, while the unchanged window
subtotal is retained as `text_window_relocations`. The README labels both.
No historical package is resurrected or rewritten.

## Actual report reproduction

Base: `9120883a957d7d9b2cab6140f66fb5bc9e6774d5`.
Environment: Python 3.12.13, pyelftools 0.32.

| Capture | Old reported total / unchanged text subtotal | Raw `.rel.dyn` rows / corrected total | Data rows omitted before |
| --- | ---: | ---: | ---: |
| Pump | 5,557 | 6,147 | 590 |
| Pump AMM | 3,904 | 4,399 | 495 |
| Pump Fees | 2,369 | 2,748 | 379 |
| Mayhem | 2,117 | 2,548 | 431 |

The probe runs all four uninstrumented analysis CLIs on unchanged captured
ELFs and runs each generated packet verifier. An independent pyelftools walk
counts the raw relocation-table rows and their `.text` address membership.
Those counts agree with the fixed report; the old reports expose only the text
subtotal. The eight before/after generated verifiers all pass.

Every unrelated summary field is identical. The complete window inventory,
call graph, function index, section-layout document and generated verifier are
byte-identical before and after. `results.json` retains their hashes, capture
identities and corrected counts.

Run this same probe against both checkouts with fresh output files:

```sh
python -B research/program-relocation-total-followup-20261101/probe.py \
  --checkout /path/to/base-checkout --output /path/to/before.json --expect base
python -B research/program-relocation-total-followup-20261101/probe.py \
  --checkout "$PWD" --output /path/to/after.json --expect fixed
python -B scripts/test_analyze_program_relocation_totals.py
```

The new regression runs all four actual CLI workflows and their raw-table
oracles in CI. This is static captured-ELF inventory accounting only. There is
no compiler, model, VM or program execution, no new binary synthesis, and no
reconstruction-gain, runtime-equivalence or security claim.
