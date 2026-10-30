# admin_cto: event holder flag and cashback operand order

This candidate changes two expressions in `programs/pump/src/creator/admin_cto.rs`:

- Compute cashback as `st.cashback && !holder`; both operands are local booleans.
- Read the event's holder flag from `a.bonding_curve.is_holder_reward`, assigned
  from `holder` earlier in the same instruction. No intervening code modifies or
  reloads that field, and the AMM CPI does not receive the bonding-curve account.

Both changes preserve validation, CPI order and event values. The 24 macro call
sites remain on their original lines.

## Verified measurements

The comparison baseline is the source inventory
`7ee4d07a5f56e1785f0183fec688a7906e625ba2793ee75a0dc014cc8c44fe1a`,
which matches main `c6519c2451bbf208ab6e1a79f6bde6b403a25638`.
A fresh identity build of this candidate produced:

| Measure | Baseline | Candidate |
| --- | ---: | ---: |
| admin_cto bytes | 27,400 | 27,400 |
| Sequence diagnostic ratio | 0.49071 | 0.49101 |
| Differing normalized instruction slots | 3,313 | 3,280 |
| Raw / normalized matched windows | 1,034 / 1,034 | 1,034 / 1,034 |

The official inventory contains 1,035 windows. No window is missing or resized,
and no existing raw or normalized match is lost. This remains a partial-window
improvement; the matched-window completion percentage does not change.

The signed admin_cto differential suite passed all 363 cases against the captured
program, including its genuine dependency CPIs. This is bounded runtime evidence,
not whole-program equivalence or whole-ELF identity.

Candidate source inventory:
`5571f6efadb7003d11becbf574ca1c21c369423f91883c1d4b3e60959d709832`.
Unstripped ELF: `ac2fb189d6152a7f74de4aa98f7a0fd8750bf8101a57d5dfd66747561f9457f6`.
Runtime ELF: `26c417379134f0397562eab011ae5c0a970492429788e9ef41080e8bef2b7ade`.

Validation used `reconstruction/harness/fastbuild.py` (identity recipe), `score.py`,
`compare_scores.py`, `target_metric.py` and `scripts/pump_admin_cto_differential.py`.
