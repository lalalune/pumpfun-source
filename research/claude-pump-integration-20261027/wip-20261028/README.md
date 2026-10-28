# Round37 composite snapshots 11/12 and completed review

These are archived research snapshots. The original capture was unverified;
the newest composite 12 has since passed the review described below. Composite
11 and the unfinished lane diffs remain historical inputs, not separately
validated deliverables. None of this promotes a maintained program source or
establishes whole-ELF identity.

| Composite 12 recipe | Genuine: normalized / raw | Synthetic layout: normalized / raw |
|---|---:|---:|
| Captured `sbpf` identity recipe, independently rebuilt byte-for-byte | 813 / 165 | 907 / 165 |
| Repository builder, `linux-v1.44-sbf` profile | 808 / 147 | 902 / 147 |

Both binaries from each recipe pass the unchanged 44-suite captured-loader
corpus: **10,468 cases, 10,464 paired diagnostic logs, zero mismatches per
binary**. These are bounded regression results, not full behavior equivalence.
The repository-builder variants have no normalized or raw window losses
against the unchanged Round37 primary source built with that same recipe.
Recipe-specific counts must not be interchanged. Matching TypeId constants
and these windows do not prove the complete historical build environment.

The `layout` variants include explicitly synthetic `// layout-pad` positioning.
The `genuine` variants contain no such padding. Source-line layout gains remain
separate from ordinary-source recovery; no original binary is used as a compiler
input.

Reviewed deliverables:

- [Genuine repository-builder package](../r37-genuine-12/README.md), including
  the source, build/control receipts, independent inventory and regression.
- [Layout repository-builder package](../r37-layout-12/README.md), with the same
  evidence and synthetic-layout qualification.
- [Identity recipe validation](../round37-12-validation/README.md), binding
  the exact snapshot binaries, rebuilt source and separate runtime reports.

Replay from the repository root with ordinary Python:

```sh
python3 -I -B research/claude-pump-integration-20261027/verify_round37_12.py
python3 -I -B research/claude-pump-integration-20261027/test_round37_12.py
```

The retained `harness/`, `tools/` and lane logs are historical build inputs.
Their absolute work paths describe the original machine; the two verification
commands above use only repository files and do not require those paths.
