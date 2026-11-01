# Mayhem Surfpool security verification

## Method

Executed **17 signed transactions** with Surfpool **1.6.1**, offline mode and signature verification enabled. Original Mayhem, Pump, PumpSwap/AMM, Fees, and captured token dependencies were loaded from their retained binaries. Each per-case artifact records loaded SHA-256 hashes, signature, error, logs, and before/after state deltas.

Original SHA-256:

- Mayhem: `a87fa9f866272514e6acb852b668c4a08aeb173d56c883039991d114d1199bdb`
- Pump: `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`
- AMM: `6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7`
- Fees: `4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e`

Privileged states were bounded by original behavior: signed global initialization and `update_trader`/`update_admin` succeeded. Per-mint creation used genuine Pump `create_v2` → Mayhem CPI, not a synthetic PDA signer. A failed account-admission probe was not treated as proof of a finding.

## Results

| ID | Status | Observed outcome |
|---|---|---|
| L-09 | **CONFIRMED** | `retained_bps=10001` produced `ProgramFailedToComplete` on both AMM sell and legacy buy; state rolled back. |
| L-10 | **CONFIRMED (Mayhem)** | Incoming nonsigner became admin; old admin then failed with `ConstraintHasOne` (2001). Pump/AMM rotation was not separately tested. |
| M-08 | **CONFIRMED** | Native sell proceeds were 182,494 lamports, but exposure moved −2,221,774: exactly 2,039,280 lamports of ATA rent was included. |
| M-10 | **INCONCLUSIVE** | Wrong-v2 buy and sell succeeded on the captured fee-exempt route. The positive-fee/nonexempt failure branch was not reached. |
| M-11 | **INCONCLUSIVE** | Ordinary native sell succeeded with the retained tail under zero creator fee. Positive-fee noncashback behavior remains untested. |
| M-18 | **CONFIRMED** | Genuine Pump CPI admitted zero-duration (immediately expired) and traderless states. Paused-at-creation is not separately claimed. |
| H-02 | **CONFIRMED** | Arbitrary first signer became canonical global admin; reinitialization failed. Fresh-deployment scope only. |
| H-05 | **CONFIRMED** | Configured trader sold through genuine ordinary native and external-quote AMM pools. No LP-profit claim or signature bypass is made. |
| H-06 | **INCONCLUSIVE** | Sell with limits 100 created stable/per-mint exposure −182,494, but the required second cross-mint buy was not constructed. |

**Counts:** 6 confirmed, 3 inconclusive, 0 blocked, 0 not reproduced.

## Key receipts

- L-09 AMM sell: `4Ddk2peWQdPvv7uQAYx4DXERLCECjYNouAqXxXb2nKu9HUD7Q9DH2d5jThf1wa23WKAn3Dib1DYLHtDgwNByK8Q9`
- L-09 legacy buy: `5eAtFzhn1pFeFAVf81oWJpVFtbadCDAt8cSBqvdCKiZALNDae3Y9M92UyoGZhkB8sSry8rnZV88GRx6KCYkx4BRk`
- M-08 native sell: `2o8BpcfFKNLroYPX9MAfanB7FAwsTyxdb9YaQikmrhXed8p9JA9TCwtC6PArT1bMzxi9CT68fYT3gdr3CtPLELd4`
- H-02 initialization: `4Q1oWcryQDFbEuu2cPdhnTgEijYVntejdrFpLQKtBCiJ2sKTNssQQcsSRQE5wTKP6oGJX54Hdnnt8tD4TKpT33ky`
- H-05 external-quote sell: `5reWpj2ikdZaaPAsvfeSVCq6jDFDgUDcRKCrqu8irdcY2xWYsZxbbh2rpxcgTjJnkKqKmnPj5rMUjLxZQ5DFjhE1`
- H-06 negative-exposure sell: `3VTdheX6g8a2g1eAQ3Fi6TEWHCKaTXiFHPyDZBkbcqBmsCdAUkUMbeFoxusK37E8siCZDU62xpqCcNkRv31cbovM`

M-10's successful wrong-PDA cases are evidence that the captured exemption masks the defect, not evidence that the positive-fee branch works. Conversely, supplying only the canonical Pump PDA fails Mayhem's own `ConstraintSeeds` (2006); that admission failure is not presented as the target Pump failure.

Full receipts are under `results/mayhem/`; the machine-readable disposition is `results/mayhem.json`.
