# admin_cto: curve field access order

This candidate changes two lines in `programs/pump/src/creator/admin_cto.rs`.
After assigning the creator, it reads the old creator fee, stores the holder flag,
and then stores the cashback flag. These are ordinary accesses to distinct fields;
there is no intervening fallible operation, CPI, serialization or account reload.
The final values and the saved old fee are unchanged. All 24 macro call sites
remain on their original lines.

## Verified measurements

The baseline source inventory is
`5571f6efadb7003d11becbf574ca1c21c369423f91883c1d4b3e60959d709832`,
verified against main `f4d156d70dec49c67a6e5bffef68379e695f5517`.
A fresh identity build of this candidate produced:

| Measure | Baseline | Candidate |
| --- | ---: | ---: |
| admin_cto bytes | 27,400 | 27,400 |
| Sequence diagnostic ratio | 0.49101 | 0.49131 |
| Differing normalized instruction slots | 3,280 | 3,280 |
| Raw / normalized matched windows | 1,034 / 1,034 | 1,034 / 1,034 |

The official inventory contains 1,035 windows. There are no missing or resized
windows and no lost raw or normalized matches. This is a partial-window sequence
improvement; the matched-window completion percentage does not change.

All 363 signed admin_cto differential cases matched the captured program using
genuine dependency CPIs. This is bounded runtime evidence, not whole-program
semantic equivalence or whole-ELF identity.

Candidate source inventory:
`d44d67269eb5ab2aaa962a2497a6552bb53254a6bb33bd0015f5d8103b62a4c0`.
Unstripped ELF: `3b87f921556f0d99afd6143641b42866489ed3e6a3006b5856b0506421053ce1`.
Runtime ELF: `f60dc66a2ee354d6a1ff98175ff74660ab80ce25573184a5dd8e60f555137286`.

Validation used `reconstruction/harness/fastbuild.py` (identity recipe), `score.py`,
`compare_scores.py`, `target_metric.py` and `scripts/pump_admin_cto_differential.py`.
