# AMM assigned-finding Surfpool results

## Environment and evidence boundary

- Target: `evidence/original/pump_amm/deployed.so`
- Loaded target SHA-256: `6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7`
- Runner: pinned `tools/surfpool`, version `1.6.1`, offline mode
- Command: `uv run --with-requirements requirements.txt python reconstruction/verification/security-surfpool/amm.py`
- All 27 submitted transactions used genuine signatures and `sigVerify=true`. No LiteSVM result is presented as Surfpool evidence. Accounts and balances are synthetic local fixtures, not live Devnet victims or configuration.
- Loaded original dependencies: Pump `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`; Fees `4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e`; SPL Token `8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697`; Token-2022 `15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d`; ATA `6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d`.
- Authoritative signatures, errors, logs, before/after account hashes, raw AMM-state bytes, lamports, token balances, and deltas: `results/amm-evidence/transactions.json`, indexed by the case names in `results/amm.json`.
- M-06 original-IDL inventory: `results/amm-evidence/initializer-inventory.json`.

**Counts after the second targeted pass: 14 CONFIRMED, 1 REJECTED, 1 INCONCLUSIVE, 1 BLOCKED (17 assigned IDs).**

## Outcome table

| ID | Status | Surfpool outcome and boundary |
|---|---|---|
| L-02 | CONFIRMED | Signed local admin stored creator-fee maximum 10,001; 10,000 control also succeeded. Administrator-gated only. |
| L-03 | CONFIRMED | Zero and -1 day lengths persisted through the zero start/end, zero supply update branch. |
| L-04 | CONFIRMED | Paused synthetic sharing state migrated the pool creator. Confirms absent guard, not ordinary permissionless reachability. |
| L-05 | CONFIRMED | Unverified metadata creator succeeded; empty vector failed. No theft or verified-only requirement supported. |
| L-06 | CONFIRMED | User-signed close with `unclaimed=5` deleted the accumulator and refunded lamports. |
| L-10 | CONFIRMED | Current admin installed a nonsigning incoming admin. |
| L-13 | CONFIRMED | Exact-input 337 debited all 337 units under the fixture fee table. |
| L-14 | CONFIRMED | Direct whitelisted buy paid no separate fee; routed buy paid 45,926 units to buyback recipient. |
| M-03 | CONFIRMED | Successful `buy_v2` created the user accumulator with `volume=0` and zero incentive counters. |
| M-04 | REJECTED | Mixed-direction route rejected custom 6086 and rolled back. Main route not directly tested. |
| M-05 | INCONCLUSIVE | Real Pump CPI committed an injected 10,001 creator fee into the AMM pool, but valid upstream creation/CTO reachability was not shown. |
| M-06 | CONFIRMED | Complete original IDL has no global-volume initializer; missing-account update fails 3012. Fresh-deployment interface gap only. |
| M-15 | CONFIRMED | Foreign-mint claim saturated the counter; separate next one-unit claim failed `Overflow` 6023. |
| M-17 | CONFIRMED | Signed admin scheduled rewards with a delegated reward vault. No live unsafe campaign tested. |
| M-19 | CONFIRMED | Fixed PUMP mint carrying synthetic PermanentDelegate was accepted as pool base. Fixed-address branch only. |
| H-08 | CONFIRMED | Canonical Pump migration admitted PermanentDelegate quote; independent delegate transferred one unit from the canonical quote vault. |
| H-09 | BLOCKED | Wrong signer rejected 6005. Fixed key unavailable; no bypass attempted. |

## Second targeted pass

### M-05 — canonical forwarding established, upstream exploit unresolved

All new migration cases used freshly signed original Pump `migrate_v2` transactions and the genuine Pump pool-authority PDA through CPI; no PDA signer was fabricated.

- Valid canonical control `5KRpFwHmaARukT1HwcLejgB3zHf8Bw2xhGDHwWaffTSp5fpLrjZCGFef9oU9cRKMMoGZpMecUWimL17GT4XH1bk4`: success; committed pool creator fee 0.
- Injected curve-field case `5nAFrKvwmHB2JbdruigrHjcAEG6d2RihBRNQz4sTCUJUnjgJynKJhr9WQVec6bTA8Pw9Rnu1bQQvGruKFx3meAhp`: success; preexisting curve `creator_fee_bps=10001` reached AMM and committed as `pool.creator_fee_bps=10001`.
- Earlier saved-route case `M-05_canonical_curve_mutation` remains in the evidence and rolled back with outer custom 6027.

This proves that AMM does not revalidate the field once the curve state exists. M-05 remains **INCONCLUSIVE** because the invalid field was injected as a fixture prerequisite, not produced by a demonstrated valid Pump creation/CTO sequence.

### M-06 — deployed-interface bootstrap gap confirmed

The complete original `pump_amm.json` instruction inventory contains `init_user_volume_accumulator`, `create_config`, `create_pool`, `init_boost`, and `admin_update_token_incentives`, but zero global-volume initializer candidates. The inventory and IDL SHA-256 are in `results/amm-evidence/initializer-inventory.json`.

The `M-06_missing_global` transaction fails custom 3012 when the global account is absent. Together these confirm the **source/deployed-IDL fresh-bootstrap gap**, not merely an admission error. They do not claim that the live canonical accumulator is absent; no live account query was made in this offline pass.

### H-08 — canonical admission and independent custody confirmed

- `H-08_ordinary_delegate_rejected`: ordinary noncanonical creation rejects PermanentDelegate with custom 6007.
- Canonical Token-2022 control `XJRpU3Asz5kJn4jcPgDcunSpHQk3fVgnBQqSb7cU2ohfdtsKxtKavAJ3ZieKQConkW1m4hZqmPGJyuCpdahMsUW`: original Pump migration and AMM pool creation succeeded without PermanentDelegate.
- Canonical PermanentDelegate migration `2vFs8cPYTGfgC7c2HSCQ8ztMesM7v5uc4cDWaSfoEomN2TUFJnLHyhgHoQfG3ZXtcEqGtYe1shbSiotNZGeKPikT`: original Pump migration admitted the delegated quote and funded the canonical AMM quote vault.
- Independent transfer `24zfbETTdog2MAeYet5qTf7kUZjo8KuNiGG57m3dranrZSu9n6kTgh6uWcgjSvPgpuQDGrFLyFyndaaBbcrunoJM`: Token-2022 `TransferChecked` signed only by the independent delegate succeeded. Canonical pool quote vault changed 67,417,750,273 → 67,417,750,272 and recipient 0 → 1. The pool owner did not sign.

H-08 is therefore **CONFIRMED** for canonical admission and retained delegate custody in this synthetic fixture. It does not establish a currently approved unsafe live mint.

## First-pass highlights

- M-15: the `M-15_saturate` case moved `cashback_claimed` from 13 to `u64::MAX`; `M-15_positive_after_saturation` failed AMM custom 6023 at `claim.rs:228`, preserving state.
- M-03: the successful buy created a 137-byte user accumulator with all incentive volume/counters zero.
- L-13: user quote delta -337, protocol recipient +2, buyback recipient +1.
- L-14: direct whitelist had no separate fee-recipient delta; routed whitelist buyback recipient gained 45,926.
- M-04: custom 6086 uniform-direction rejection and rollback.

Full transaction signatures and logs for these cases are in the authoritative evidence JSON.

## Interpretation limits

`CONFIRMED` confirms the assigned behavior in the documented fixture, not old severity, a live production exploit, current Devnet configuration, or quantified loss. Administrator cases use locally owned fixture admins with real signatures. Fixed-address mint state proves admission semantics only. Setup/admission errors were not promoted to confirmations. H-09 remains **BLOCKED**, and no claim about the Main M-04 route is made without direct evidence.
