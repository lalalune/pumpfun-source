# Pump Main Surfpool security results

Target: `evidence/original/pump/deployed.so`, SHA-256 `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`, executed offline with pinned Surfpool 1.6.1 and original dependencies. All target transactions had genuine test-owned signatures and `sigVerify=true`; no simulation signature bypass was used. Fixtures are synthetic, not live deployment or current-production-state claims.

**Counts: 12 CONFIRMED, 2 REJECTED, 0 INCONCLUSIVE, 0 BLOCKED (14 assigned IDs).**

| ID | Status | Surfpool result |
|---|---|---|
| L-01 | CONFIRMED | Paused sharing config migrated successfully; no Active guard. Exceptional synthetic state only. |
| L-06 | CONFIRMED | User-signed close erased 123 pending units, refunded 2,844,400 lamports, and preserved token-cashback ATA. |
| L-16 | CONFIRMED | Migration accepted donated intermediate-ATA base in initial liquidity; profitable extraction not shown. |
| M-01 | CONFIRMED | Residual-one route charged full 14 budget; curve real quote reached 12 and lamports increased 14. |
| M-02 | CONFIRMED | Successful `buy_v2` left UserVolumeAccumulator bytes unchanged. |
| M-06 | CONFIRMED | Fresh scheduling failed with `AccountNotInitialized` (3012); current Devnet absence not asserted. |
| M-14 | CONFIRMED | Native 10^18 distribution failed with `Overflow` (6024) before division. |
| M-15 | CONFIRMED | Main-only: foreign-mint claim saturated counter; next positive claim panicked; native claim remained usable. |
| M-16 | CONFIRMED | Nonnative `create_v2` accepted zero virtual quote reserves. Purchase pricing not exercised. |
| M-17 | CONFIRMED | Admin scheduling accepted a Token-2022 PermanentDelegate reward mint. Admission only. |
| H-01 | REJECTED | A→WSOL→native-B failed AMM `MultiHopMixedDirection` (6086); isolated WSOL-output buy failed `OnlyPumpPools` (6078). Ordinary two-buy control succeeded, so the claimed route cannot reach Main. |
| H-03 | REJECTED | Actual 1% Token-2022 fee migration completed, including CreatePool and withheld-fee harvest; no second subtraction is needed. |
| H-04 | CONFIRMED | Arbitrary signer initialized fresh Global and became authority; existing-state overwrite not claimed. |
| H-08 | CONFIRMED | Approved external quote with PermanentDelegate was admitted by `create_v2`; no live drain claimed. |

Per-case artifacts under `main-cases/` record loaded binary hashes, transaction signatures, exact errors, logs, and watched-account deltas. `main.json` contains the scoped evidence and artifact index. Reproduce with:

```bash
uv run --with-requirements requirements.txt python reconstruction/verification/security-surfpool/main.py
```
