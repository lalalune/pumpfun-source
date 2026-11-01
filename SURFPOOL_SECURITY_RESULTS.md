# Original-binary Surfpool security validation

**Validation date:** 2026-10-31  
**Runtime:** Surfpool 1.6.1, offline mode  
**Scope:** All 47 findings in `SECURITY_REPORT.md`, using the retained original Pump.fun program binaries and synthetic local accounts

## Result

| Disposition | Findings | Meaning |
|---|---:|---|
| **CONFIRMED** | **39** | The described code behavior was reproduced under the documented fixture. This does not by itself confirm the old severity, a live deployment condition, or profitable exploitation. |
| **REJECTED** | **3** | The claimed exploit/failure route was blocked or the opposite behavior completed successfully on the original binaries. |
| **INCONCLUSIVE** | **4** | A required branch or complete exploit sequence was not established; neither confirmation nor rejection is claimed. |
| **BLOCKED** | **1** | The fixed AMM administrator private key is unavailable, so legitimate bootstrap could not be signed. |
| **Total** | **47** | Every finding received a targeted Surfpool test lane. |

The most important negative results are:

- **H-01 rejected:** mixed sell→buy routing failed `MultiHopMixedDirection` (6086); an isolated WSOL-output buy failed `OnlyPumpPools` (6078). An ordinary two-buy control succeeded.
- **H-03 rejected:** a 1% Token-2022 transfer-fee migration completed end-to-end, including AMM pool creation and withheld-fee harvesting. `TokenAccount.amount` is already spendable balance; the proposed second withheld-fee subtraction is incorrect.
- **M-04 rejected:** the tested intermediate-sell route failed the uniform-direction check with custom error 6086 and rolled back. No admitted route demonstrated double deduction.

The strongest confirmed availability/economic behaviors include Main and AMM foreign-mint cashback-counter poisoning (M-15), Pump completion-budget overcharge (M-01), Relay donation overflow (M-09), Relay fee-on-transfer settlement underfunding (M-13), Relay pre-created ATA denial (C-01), whitelisted PermanentDelegate drainage (C-02), and WSOL residual native-burn failure (C-03), subject to the fixture and authority limitations below.

## Original binaries

| Program | Retained file | SHA-256 |
|---|---|---|
| Pump Main | `evidence/original/pump/deployed.so` | `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d` |
| PumpSwap / AMM | `evidence/original/pump_amm/deployed.so` | `6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7` |
| Fees | `evidence/original/pump_fees/deployed.so` | `4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e` |
| Mayhem | `evidence/original/mayhem/deployed.so` | `a87fa9f866272514e6acb852b668c4a08aeb173d56c883039991d114d1199bdb` |
| Donation Relay | `evidence/dependencies/donation_relay/deployed.so` | `367f07a62e3f74d358187d175cf3228848e81a56c781a9a75b9df7fed1268563` |

Original SPL Token, Token-2022, Associated Token, Token Metadata, and other retained dependencies were loaded where required. Individual receipts record the exact loaded hashes, transaction signatures, errors, logs, and state deltas.

## Complete 47-finding matrix

| ID | Disposition | Original-binary Surfpool result and boundary |
|---|---|---|
| L-01 | CONFIRMED | Main creator migration accepted a synthetic paused sharing config and changed the curve creator. This proves the missing status guard, not ordinary reachability of that paused state. |
| L-02 | CONFIRMED | Signed AMM admin stored a 10,001-bps creator-fee maximum; administrator-gated configuration behavior only. |
| L-03 | CONFIRMED | AMM persisted zero and −1 incentive day lengths through the zero-range update branch. |
| L-04 | CONFIRMED | AMM accepted a synthetic paused sharing config during creator migration; ordinary paused-state reachability is not claimed. |
| L-05 | CONFIRMED | AMM accepted an unverified metadata creator; an empty creator vector panicked. Robustness is confirmed, not a theft path or verified-only policy. |
| L-06 | CONFIRMED | Main and AMM user-signed close deleted accumulators with pending incentives and refunded rent. Main preserved token-cashback assets; no external close authority was shown. |
| L-07 | CONFIRMED | Original Fees empty normal/stable tier queries panicked with index-out-of-bounds. |
| L-08 | CONFIRMED | Fees old authority rotated without incoming signature; old authority subsequently failed and new authority succeeded. |
| L-09 | CONFIRMED | Mayhem `retained_bps=10001` produced `ProgramFailedToComplete` on AMM sell and legacy buy; state rolled back. |
| L-10 | CONFIRMED | AMM and Mayhem current admins installed nonsigning incoming admins. Operational lockout remains conditional on losing the new key. |
| L-11 | CONFIRMED, LIMITED | Relay stub route rejected zero output with 6023 but accepted one unit, confirming no independent output floor. No real-Jupiter slippage bypass was demonstrated. |
| L-12 | CONFIRMED, POST-AUTH | Signed unsolicited debouncer credit remained unaccounted; simulated settlement burned a separate distribution residual after distributing recorded principal. |
| L-13 | CONFIRMED | AMM exact-input 337 case debited all 337 units; fee recipients gained 2 and 1 under the fixture fee table. |
| L-14 | CONFIRMED | Direct whitelisted AMM buy paid no separate fee; routed buy paid 45,926 units to the buyback recipient for the same signer. |
| L-15 | CONFIRMED | Fees readonly social authority failed recipient-ATA creation with `PrivilegeEscalation`. Readonly extension funding succeeded, so the defect is branch-specific. |
| L-16 | CONFIRMED | Main migration included donated intermediate-ATA base in initial liquidity. No profitable donor extraction was demonstrated. |
| M-01 | CONFIRMED | Pump completion-boundary route charged full budget 14 while real quote reserves reached 12; curve lamports increased by 14. |
| M-02 | CONFIRMED | Successful Main `buy_v2` changed trade balances but left UserVolumeAccumulator bytes unchanged. |
| M-03 | CONFIRMED | Successful AMM `buy_v2` created/retained user volume accounting at zero despite a balance-changing trade. |
| M-04 | REJECTED | Tested mixed-direction route failed custom 6086 before the claimed double-fee behavior. |
| M-05 | INCONCLUSIVE | Original Pump migration forwarded an injected invalid 10,001 creator fee, but no valid upstream route to that malformed curve state was established. |
| M-06 | CONFIRMED | Main and AMM fresh scheduling failed missing global-volume account with 3012; original IDL/initializer inventory found no global-volume initializer. No live-state absence is asserted. |
| M-07 | CONFIRMED | Fees legacy-sized stable update succeeded and changed bytes, but reload saw zero stable tiers and query panicked. |
| M-08 | CONFIRMED | Mayhem native sell proceeds were 182,494 lamports while exposure moved −2,221,774: exactly 2,039,280 lamports of trader-funded ATA rent was included. A free risk-limit bypass is not claimed. |
| M-09 | CONFIRMED | Signed Relay 10^18 donation failed `ArithmeticOverflow` 6008; 10^16 control succeeded. Atomic denial only, not existing-fund loss. |
| M-10 | INCONCLUSIVE | Wrong-v2 Mayhem buy/sell succeeded on the captured fee-exempt route; the required positive-fee/nonexempt target branch was not established in the finalized evidence. |
| M-11 | INCONCLUSIVE | Ordinary Mayhem AMM sell succeeded with zero creator fee; the specific positive-fee noncashback pool-v2 omission failure was not established. |
| M-12 | CONFIRMED | Fees Token-2022 donation PDA creation succeeded; crank failed `IncorrectProgramId` in legacy SPL Token before Relay settlement. |
| M-13 | CONFIRMED, POST-AUTH/STUB | Net 900,000 donation became 810,000 distribution funds; exact 900,000-input Token-CPI swap failed insufficient funds. Real Jupiter was not used. |
| M-14 | CONFIRMED | Main native 10^18 creator-fee distribution failed `Overflow` 6024 before division. |
| M-15 | CONFIRMED | Main and AMM foreign-mint claims saturated shared counters to `u64::MAX`; subsequent positive claims failed overflow. Main native cashback remained usable. |
| M-16 | CONFIRMED, ADMISSION | Main nonnative `create_v2` accepted zero virtual quote reserves. Purchase pricing was not exercised. |
| M-17 | CONFIRMED, ADMISSION | Main accepted a PermanentDelegate reward mint; AMM accepted scheduling with a delegated reward vault. No live unsafe campaign was asserted. |
| M-18 | CONFIRMED | Genuine Main→Mayhem CPI admitted zero-duration/immediately expired and traderless per-mint states. |
| M-19 | CONFIRMED, SYNTHETIC | AMM accepted the fixed PUMP mint carrying synthetic PermanentDelegate as pool base. No claim is made about the live mint's extension state. |
| H-01 | REJECTED | Mixed direction failed 6086; isolated WSOL-output buy failed 6078; ordinary two-buy control succeeded. The proposed accounting route was not admitted. |
| H-02 | CONFIRMED | Arbitrary first signer initialized Mayhem GlobalParams and became admin; reinitialization failed. Fresh-deployment scope only. |
| H-03 | REJECTED | Actual 1% Token-2022 fee migration completed including pool creation and withheld-fee harvest. The claimed gross/spendable mismatch did not occur. |
| H-04 | CONFIRMED | Arbitrary signer initialized fresh Main Global and became authority; existing-state overwrite is not claimed. |
| H-05 | CONFIRMED, VENUE | Configured Mayhem trader sold through genuine ordinary native and external-quote AMM pools. LP-withdrawal profit was not demonstrated. |
| H-06 | INCONCLUSIVE | External-quote sell produced negative stable/per-mint exposure, but the required second different-mint buy did not produce finalized target evidence. |
| H-07 | CONFIRMED, POST-AUTH | Signed non-whitelisted pausable-mint donation and independent pause committed; simulated close then failed Token-2022 custom 67. |
| H-08 | CONFIRMED, SYNTHETIC CANONICAL | Main admitted approved PermanentDelegate quote; canonical migration enabled independent delegate transfer without pool-owner authorization. No unsafe live approved mint is asserted. |
| H-09 | BLOCKED | Wrong AMM bootstrap signer failed `InvalidAdmin` 6005. Fixed administrator private key is unavailable, so legitimate bootstrap could not be executed. |
| C-01 | CONFIRMED, POST-AUTH | Signed Relay donation and outsider ATA precreation committed; simulated authorized close failed `IllegalOwner` without state advancement. |
| C-02 | CONFIRMED, CONDITIONAL | Signed whitelisted PermanentDelegate donation and independent delegate transfer of 1,000,000 units both committed. Requires whitelist approval and delegate control. |
| C-03 | CONFIRMED, POST-AUTH/STUB | Exact-input stub swap left 777 WSOL; Relay residual native Burn failed SPL Token custom 10. This isolates Relay behavior, not end-to-end Jupiter execution. |

## Evidence boundaries

- Main, AMM, Fees, and Mayhem target transactions used genuine test-owned signatures with `sigVerify=true`. No production signature bypass was used.
- Relay donor and attacker actions were genuinely signed and committed. The production relayer key is unavailable, so privileged Relay calls were Surfpool simulations with `sigVerify=false`. These establish post-authorization behavior only, not a signature bypass or committed privileged freeze.
- Real Jupiter was not available. L-11, M-13, and C-03 used an explicitly labeled Token-CPI stub at the Jupiter address to isolate Relay pre/post-CPI behavior. They are not end-to-end Jupiter proofs.
- All accounts, authorities, mint configurations, reserves, and balances are synthetic local fixtures. A confirmed behavior does not establish current Devnet/Mainnet configuration, live key ownership, current TVL exposure, profitable extraction, or the report's previous severity assignment.
- Rejected means the tested claimed route/result was not supported; it is not a formal proof that every conceivable variant is impossible. Inconclusive and blocked cases must not be represented as verified vulnerabilities.

## Reproduction and artifacts

Run each lane from the repository root:

```bash
uv run --with-requirements requirements.txt python reconstruction/verification/security-surfpool/main.py
uv run --with-requirements requirements.txt python reconstruction/verification/security-surfpool/amm.py
uv run --with-requirements requirements.txt python reconstruction/verification/security-surfpool/fees.py
uv run --with-requirements requirements.txt python reconstruction/verification/security-surfpool/mayhem.py
uv run --with-requirements requirements.txt python reconstruction/verification/security-surfpool/relay.py
```

Detailed per-program results:

- `reconstruction/verification/security-surfpool/results/main.md` and `main.json`
- `reconstruction/verification/security-surfpool/results/amm.md` and `amm.json`
- `reconstruction/verification/security-surfpool/results/fees.md` and `fees.json`
- `reconstruction/verification/security-surfpool/results/mayhem.md` and `mayhem.json`
- `reconstruction/verification/security-surfpool/results/relay.md` and `relay.json`

The pinned Surfpool executable and its downloaded archive are under `reconstruction/verification/security-surfpool/tools/`. The shared RPC/fixture harness is `surfpool_rpc.py`; `smoke.py` verifies signed original-Pump initialization independently.
