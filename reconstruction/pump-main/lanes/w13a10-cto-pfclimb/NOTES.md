# admin_cto: PDA ordering, lazy sweep and rent expression

This candidate changes three lines in `programs/pump/src/creator/admin_cto.rs`:

- Compute the holder PDA after the local sharing-state reads. The PDA inputs and
  subsequent validation are unchanged.
- Express the sweep as `(!skip).then(...).transpose()?.unwrap_or(0)`. The closure
  runs exactly once when `!skip`; its error propagates and a skipped sweep returns zero.
- Read the minimum rent balance directly from `Rent::get()?` in the same native
  branch, without retaining a local reference to the plain `Rent` value.

The existing borrowed argument copy and event flags read from the curve remain.
These changes preserve validation, CPI order and values. All 24 macro sites
retain their original line numbers.

## Verified measurements

The review includes current main `1f1a717091798e3d3e5ff31a9bd1398d4ac4b08e`,
whose full Pump source inventory is
`976a6bf25dd46c867047081de1bc0a0ff758ff0e3dc0a7192d200f7ce1d1e430`.
A fresh identity build produced:

| Measure | Baseline | Candidate |
| --- | ---: | ---: |
| admin_cto bytes | 27,400 | 27,400 |
| Sequence diagnostic ratio | 0.49431 | 0.50929 |
| Differing normalized 8-byte slots | 3,306 | 3,325 |
| Raw / normalized matched windows | 1,034 / 1,034 | 1,034 / 1,034 |

The sequence ratio improves while the positional mismatch count increases.
The official 1,035-window inventory has no missing or resized windows and no
lost raw or normalized matches. This is a partial-window improvement; it does
not increase the matched-window completion percentage or prove whole-ELF identity.

All 363 signed admin_cto differential cases matched the captured program with
genuine dependency CPIs. This is bounded runtime evidence, not all-input proof.

Source inventory: `acc7d171b7b95e86658ed1403884b354746028559b267e0ed9bf3d0cda57393e`.
Unstripped ELF: `e06cef03802a9473f5de5b40ff1ae07d527fed899c7ed52d59a2a32633e9d702`.
Runtime ELF: `b0ab591683f953051dd8e2a1a94449459872baa63c537f8850d3ca75f5220afd`.

Validation used `reconstruction/harness/fastbuild.py` (identity recipe), `score.py`,
`compare_scores.py`, `target_metric.py` and `scripts/pump_admin_cto_differential.py`.
