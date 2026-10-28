Research packet composing parallel Claude lane recoveries on the maintained **Round37** main-Pump source. It adds only `research/claude-pump-integration-20261027/r37g4/`; `programs/pump`, rounds and status files are untouched.

**744 → 780 normalized** and **121 → 147 raw** windows. The baseline is a control build of the unchanged Round37 primary source with the same repository builder (`linux-v1.44-sbf` profile), which this packet ships. There are **no normalized or raw losses**. Against the published Round37 inventory the packet gains 36 normalized windows and loses none. Raw counts use the plain link; the published round adds derived text-order linker scripts. Built with the original's Linux `sbpf-solana-solana` libraries (PR #307), the same source reaches **785 normalized / 164 raw**. Whole-ELF identity remains false.

| lane | windows | change |
|---|---|---|
| pump-hi | 25 | Round37-aware tools/apply_lane_changes.py --with-cpi-7 --with-fee-8 (items already in Round37 are skipped; Round37's own idls/pump_fees.json and pump_fees client are kept): const-generic legacy buy, SetMayhemVirtualParams layout and handler… |
| pump-mid | 1 | CurveHop constraint compares quote_mint.key()==bonding_curve.quote_mint. |
| pump-lo | 1 | CollectCreatorFeeV2: exported creator-fee collector taking system_program as &AccountInfo (no argument promotion) and emitting the event by reference. That lane independently reproduced the nearmiss changes below (its p02-p04). |
| nearmiss | 4 | require_gt! operand bound before the macro; exported native-payment helpers (external linkage blocks ArgumentPromotion); v2 rent helper keeps an unused leading argument and uses the shared transfer. |
| nearmiss2 | 1 | u128 numerator via checked_add(..).ok_or(Overflow)? before checked_mul. |
| libinst | 4 | MigrateV2 harvests withheld Token-2022 fees through a pub wrapper around anchor_spl::token_2022_extensions::harvest_withheld_tokens_to_mint. |
| hostid | raw/order | Removes two constructs the original does not contain: runtime pubkey! base58 decoding in create_v2::execute (now consts on the existing MAYHEM_ID line) and u128 Display formatting from a require_gt! on a u128 operand in trade_v3.rs (narrowe… |

Runtime validity: the build log has no `Stack offset ... exceeded max offset` warning. migrate_v2 keeps Round37's hand-built CPIs, because generated clients inside `migrate_v2::execute` overflowed the 4 KiB SBF frame in an earlier composite.

Regression: the 44-suite captured-loader corpus passes against this exact candidate in a single `scripts/pump_validate_parallel.py --captured-loader` run: 10,468 cases, 10,464 paired diagnostic logs, 0 mismatches (`full.json.gz`).

The packet contains both ELFs, the full compiled crate and its exact `source.patch` against Round37's archived primary, the control build, `inventory.json.gz`, the builder's `build-attempt.json` / `build-comparison.json` binding, and a pure-Python `verify.py`.

```sh
python research/claude-pump-integration-20261027/r37g4/verify.py
```

This supersedes the Round36-based #323 for promotion purposes, since the same lane changes are re-applied here on Round37.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
