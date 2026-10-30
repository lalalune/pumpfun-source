# admin_cto: read the old fee before updating the curve

This candidate reads `old_fee` immediately after `old_creator`, before the creator
and boolean fields are stored. The fields are independent ordinary struct fields;
there is no intervening fallible operation, CPI or serialization. The saved fee,
final curve values and event fields are unchanged. All 24 macro call sites retain
their original line numbers.

## Verified measurements

The reviewed branch includes main `4150e64b2eb5182818554c0a217d1858210aa278`,
whose full Pump source inventory matches the verified #2933 build:
`e3c9b449d89df914be23f8ba7f42027ae27a6f25e1b6fa25f938f0bc1dae6275`.

| Measure | Baseline | Candidate |
| --- | ---: | ---: |
| admin_cto bytes | 27,400 | 27,400 |
| Sequence diagnostic ratio | 0.51348 | 0.51378 |
| Differing normalized 8-byte slots | 3,334 | 3,334 |
| Raw / normalized matched windows | 1,034 / 1,034 | 1,034 / 1,034 |

A fresh identity build and official score preserve every existing raw and
normalized match across the 1,035-window inventory, with no missing or resized
windows. This is a partial-window improvement; the matched-window completion
percentage is unchanged and whole-ELF identity is not established.

All 363 signed admin_cto differential cases matched the captured program with
genuine dependency CPIs. This is bounded runtime evidence, not all-input proof.

Source inventory: `ac3b17af3f7a2b1b703787c4aa7f426625bfe9f6698dc11a926692193c9e8415`.
Unstripped ELF: `fed5e08665b16d4814c485464835b5c1617da8f7b1a4bb5c6222246ab1d3d35b`.
Runtime ELF: `da5b3a9a62611eb898153cd715faa4fc9b96fab7a75a4f784034e478a77eb01f`.

Validation used `reconstruction/harness/fastbuild.py` (identity recipe), `score.py`,
`compare_scores.py`, `target_metric.py` and `scripts/pump_admin_cto_differential.py`.
