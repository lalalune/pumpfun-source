# admin_cto: earlier argument copy and event flags

The borrowed `new` tuple is bound before the function-scope `CtoState` literal.
Both operations read plain values without side effects. The event reads the
holder and cashback flags from the local variables that were stored into the
curve earlier in the instruction. There is no intervening curve-field mutation
or reload, so the emitted values are unchanged. All 24 macro sites retain their
original line numbers.

## Verified measurements

The reviewed branch includes main `4d529362b74a2051a5a164b7e251cb90eb9cccf5`,
whose full Pump source inventory matches the verified #2921 build:
`acc7d171b7b95e86658ed1403884b354746028559b267e0ed9bf3d0cda57393e`.
A fresh identity build produced:

| Measure | Baseline | Candidate |
| --- | ---: | ---: |
| admin_cto bytes | 27,400 | 27,400 |
| Sequence diagnostic ratio | 0.50929 | 0.51228 |
| Differing normalized 8-byte slots | 3,325 | 3,334 |
| Raw / normalized matched windows | 1,034 / 1,034 | 1,034 / 1,034 |

The sequence ratio improves while the positional mismatch count increases.
The official 1,035-window inventory has no missing or resized windows and no
lost raw or normalized matches. This partial-window change does not increase
the matched-window completion percentage or establish whole-ELF identity.

All 363 signed admin_cto differential cases matched the captured program with
genuine dependency CPIs. This is bounded runtime evidence, not all-input proof.

Source inventory: `6ec93b9004c2374f087c98d93a6d5bc3c211ef133999b84a0e995b8b080a3761`.
Unstripped ELF: `89dc0ae69faf3fd63f2691b76f35a6bcfe144988598454eff1bc0dc3a8fe088c`.
Runtime ELF: `2b3bc21e534a0180f6cb838c9cb087b4c7eda4a51da7a1f4d66c4bf613084853`.

Validation used `reconstruction/harness/fastbuild.py` (identity recipe), `score.py`,
`compare_scores.py`, `target_metric.py` and `scripts/pump_admin_cto_differential.py`.
