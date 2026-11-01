# Security audit — second pass, 2026-10-30

**Assessment:** No new CRITICAL vulnerability was confirmed. Two additional vulnerable paths were identified in the initial source: a HIGH Relay settlement blocker and a MEDIUM Main cashback-counter denial of service. Both now have source-level mitigations in the concurrently edited working tree. This is not release approval: a refreshed complete-program build still fails.

The other agent is actively modifying contracts. This report distinguishes the initial source at `2703846d3265e704040162d7e73b92f8540d7f75` from the current, uncommitted remediation. Do not add these rows to the first report's counts without reconciling source versions and overlapping root causes.

| Severity | Finding | Initial source | Working-tree observation |
|---|---|---|---|
| LOW | No separate new finding promoted | — | — |
| MEDIUM | S2-M01 — Main shared cashback counter can block unrelated token claims | Vulnerable | Nonblocking arithmetic passes focused regression tests |
| HIGH | S2-H01 — Relay requires fresh creation of predictable associated token accounts | Vulnerable by source/dependency trace | All three relevant contexts now use constrained `init_if_needed`; defensive source checks pass |
| CRITICAL | No new finding confirmed | Full transaction reproduction not established | No certification of absence |

## S2-M01 — Main cashback statistics can block valid claims

**Locations:** `programs/lalalune/src/token_incentives/claim_token_incentives.rs:130-142,305-347`; initial `programs/lalalune/src/token_incentives/volume_accumulator.rs:180-193`.

The initial nonnative cashback path accepted arbitrary token mints and a nonsigning beneficiary. It combined raw token amounts from different mints in one checked `u64` counter. Unsolicited valueless tokens could exhaust that counter, after which otherwise valid positive token claims reverted. Native claims use a separate counter. No theft or cross-user vault withdrawal was found.

**Severity:** MEDIUM: targeted availability loss, with accumulator recreation potentially available but disruptive to pending reward rights. This extends the AMM counter-poisoning class reported as M-16 in the first pass to Main; treat their common cause consistently.

**Remediation observed:** `record_cashback_claim` now uses saturating, nonblocking statistics. Seven tests passed against a saved baseline module and the current module, including preservation of valid claims after counter saturation. Aggregate raw-unit statistics across arbitrary mints remain unsuitable for economic reporting; per-mint counters are preferable.

**Limit:** These tests validate the arithmetic and regression. Complete account admission, token movement, and Solana transaction execution were not replayed end to end.

## S2-H01 — Relay associated-account initialization can block epoch closure

**Initial locations:** `programs/donation-relay/src/instructions/v1/relayer_only/close_donation_epoch.rs:17-20`; `distribute/just_swap.rs:36-37`; `distribute/swap_then_distribute.rs:13-14` under the same `relayer_only` directory.

The initial contexts used non-idempotent `init` for canonical associated token accounts whose addresses are predictable before the distribution account exists. Associated-account creation does not require the token authority's signature. A correctly initialized account can therefore exist before the Relay attempts to create it. The resolved Anchor creation path uses the ordinary associated-token Create instruction, which rejects an already token-owned account.

On epoch closure this happens before the handler can increment the current epoch or transfer the recorded donations to a distribution. The existing debouncer principal remains pending, and the normal settlement paths require the distribution state that failed to initialize. The reviewed live instruction surface does not expose a separate refund, epoch-skip, or arbitrary vault-close operation for this state. This is an availability defect affecting a configuration/mint pair, including ordinary supported mints; it does not require a malicious token issuer or a relayer signature from the party causing the account to exist.

**Severity:** HIGH for a permissionless principal-settlement blocker in the initial instruction set. No direct theft was demonstrated. A broader CRITICAL claim about permanent, protocol-wide freezing requires stronger complete-program execution and recovery analysis than this pass established.

**Remediation observed:** All three contexts now use `init_if_needed` while retaining canonical mint, authority, and token-program constraints. Five defensive checks passed: these three account declarations plus the Main and Mayhem bootstrap authority guards. This confirms the source change, not the full account lifecycle at runtime.

**Required transaction regressions before release:** legitimate settlement with both absent and already valid accounts; rejection of incorrect mint/authority/program; pre-existing balances; duplicate-account behavior; successful epoch advance; and the complete subsequent distribution/closure lifecycle. Automatic safety review blocked the planned exploit-oriented replay, so no such replay is claimed here.

## Conditional HIGH-impact quote-token trust risk

The AMM review also found that both main/native mint-policy parsers can admit `PermanentDelegate` on an external quote mint when the extension-enabled policy is selected. A quote issuer retaining that capability has custody powers over pool-owned quote tokens, and this can damage the paired base inventory rather than only the issuer's own asset.

The saved AMM packet contains three passing native/processor tests, including actual SPL delegate semantics and production pool-math observations. **An administrator must first approve the external quote mint.** No public bypass of quote approval or substitution into immutable Main-issued ancestry was established. This is therefore recorded as a conditional HIGH-impact issuer-trust hazard, not as a confirmed permissionless CRITICAL exploit or an additional unconditional finding.

Review quote approval against an explicit supported-extension policy. Reject asset-seizure capabilities unless the product deliberately accepts and discloses that issuer trust. Do not assume that a quote mint with revoked mint/freeze authority lacks other authority mechanisms.

## Remediation checks and negative results

- Main and Mayhem initialization now bind the initializer to the program's actual upgrade-authority record. Both source guards passed; no complete deployment/initialization transaction was tested.
- The Fees defensive suite passed seven tests covering fail-closed fee selection, stable-layout capacity, invalid-update nonmutation, nonblocking counters, actual incoming-authority account constraints, and generated writable/signer metadata.
- Main account-alias review did not establish another unprivileged drain. Real source and destination authority relationships prevent the examined self-transfer and cross-user accumulator substitutions.
- Lifecycle review did not find a new mint-authority or Mayhem vault-signer leak. Fixed CPI targets, stored trader/admin checks, and downstream ATA/mint checks remain material controls.
- The Anchor 1.0 `Program<System>` default-ID concern did not establish arbitrary CPI: the inspected System helpers construct canonical System instructions rather than using the supplied context's program ID.
- Migration and creator-authority paths did not yield an additional independently confirmed theft path. Previously rejected mixed-direction route and donor-profit claims were not reinstated.

## Verification and source provenance

**19 focused defensive/counter checks passed:** seven Main tests, seven Fees tests, and five source-guard checks. The separate AMM packet contains three further passing native/processor tests. None is a complete five-program integration run.

A refreshed `cargo check --workspace --offline` still failed, now reporting 45 Fees compilation errors beginning with missing CPI IDLs. The root workspace covers Fees and its math package only. Pure helper tests and generated-context checks do not establish successful deployment, CPI ABI compatibility, SBF compute/stack acceptance, or correct signer configuration on a real deployment.

Durable evidence is under `/Users/shawwalters/.codex/audits/lalalune-source-20261030-pass2/`:

- `root/source-inventory.json`, `root/snapshot/`, and `root/working-tree.patch`: working-tree snapshot during remediation.
- `root/remediation-guard-hashes.json` and `root/remediation-guard-tests.log`: exact versions checked for the five source guards.
- `root/fees-regression-tests.log` and `root/workspace-check.log`: refreshed verification.
- `main-alias/REVIEW.md` and `main-alias/tests.log`: baseline/current counter and alias evidence.
- `lifecycle/REVIEW.md`: lifecycle hypotheses and negative checks.
- `amm/test.log`: conditional quote-issuer capability observations; full-program replay is not claimed.

These conclusions are bounded by the recorded hashes. Other-agent changes after those checks need revalidation. This pass changed audit documentation and evidence only; remediation edits belong to the other agent. No deployment or chain transaction was performed by this review.
