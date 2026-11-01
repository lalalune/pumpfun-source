# Pump.fun Smart-Contract Security Review

## Pump Main

## Completion fallback charges the full budget instead of exact cost

At the completion boundary, optional post-fill returns `None`, and fallback accounting uses the original full budget even though base output is capped. Charged 14 quote units while exact completion cost 12; curve lamports increased by 14.

**Reproduction:** Execute a public one-hop completion-boundary trade whose residual net amount is below 2 or whose post-output is zero. Compare the caller's debit and curve reserves with exact completion cost.

**Remediation:** Return exact completion accounting independently of optional post-fill.

```rust
let completion_quote = exact_completion_cost(&curve, base_out)?;
let post_fill = optional_post_fill(...);
charge_quote(completion_quote + post_fill.unwrap_or(0))?;
```

## Trading does not record incentive volume

The only production accumulator update is the claim path with zero new volume. A successful signed `buy_v2` changed balances but left UserVolumeAccumulator bytes unchanged. User impact requires an intended active, funded campaign.

**Reproduction:** Fund and enable an incentive campaign, execute an eligible trade, advance the reward day, and attempt to claim. Observe that the trade created no volume entitlement.

**Remediation:** Record eligible quote volume exactly once per intended trade, preserving opt-in and denomination rules. Add a funded trade → rollover → payout integration test.

```rust
volume_accumulator::update(
    ctx,
    eligible_quote_volume,
    Clock::get()?.unix_timestamp,
)?;
```

## Creator-fee distribution overflows before division

Native and token distributions multiply the full raw balance by share basis points in `u64` before division. Surfpool reproduced `Overflow` with a `10^18` balance and 10,000-bps share although the final payout fits. High-decimal assets can reach the raw-unit boundary without equivalent economic value.

**Reproduction:** Fund a creator-fee account with `10^18` raw units and distribute a 100% share. The intermediate multiplication fails before payout.

**Remediation:** Widen before multiplication and narrow only after division.

```rust
let payout = u64::try_from(
    (balance as u128)
        .checked_mul(share_bps as u128)
        .ok_or(ErrorCode::Overflow)?
        / 10_000,
).map_err(|_| ErrorCode::Overflow)?;
```

## Foreign-mint cashback claims poison shared counters

A nonsigning victim and caller-selected nonnative mint allow anyone to add attacker-supplied token units to the victim's checked stable-cashback counter. Main and AMM counters saturated to `u64::MAX`; subsequent positive claims overflowed. Tokens still transfer to the victim, and Main native cashback remains usable through its separate counter.

**Reproduction:** Create a high-supply mint, fund its deterministic cashback ATA, and claim to a victim without the victim's signature. Repeat with any positive genuine token claim after saturation; the second claim fails.

**Remediation:** Make telemetry nonblocking as immediate containment. Recognize intended assets or use per-mint statistics without stranding legitimate balances. If recovery uses close/recreate, settle incentive rights first and combine it with genuine payout where possible.

```rust
// Containment: accounting failure must not block asset payout.
stable_claimed = stable_claimed.saturating_add(amount);
// Preferred: separate statistics by recognized mint and claim category.
```

***

# PumpSwap / AMM

## Swaps do not record incentive volume

**Final score: Medium — Likelihood: High; Impact: Medium.**

The only production accumulator update is claim with zero volume. A successful signed `buy_v2` created or retained user accounting at zero despite a balance-changing trade. User impact requires an intended active, funded campaign.

**Reproduction:** Execute an eligible funded-campaign swap, roll over the reward day, and attempt payout; no trade volume was accrued.

**Remediation:** Define eligible directions and quote denomination, record actual swaps once, and test swap → rollover → payout.

```rust
volume_accumulator::update(ctx, eligible_quote_volume, now)?;
```

***

# Fees

## Stable-fee updates disappear on legacy-sized accounts

**Final score: Medium — Likelihood: Medium; Impact: Medium.**

A stable-fee update on a legacy 2512-byte FeeConfig succeeded and changed bytes, but reload decoded zero stable tiers and a query panicked. Small writes remain invisible; oversized serialization fails rather than silently truncating.

**Reproduction:** Update stable tiers on a legacy-sized account, reload it, and query stable fees. Extend then reapply as a repair control.

**Remediation:** Require the correct layout/version before updates; migrate by extending and reapplying. Test reload, query, and preservation of normal tiers.

```rust
require!(fee_config.supports_stable_fees(), ErrorCode::LayoutMigrationRequired);
```

## Token-2022 quote donations cannot be cranked

**Final score: Medium — Likelihood: Medium; Impact: Medium.**

Creator/admin-authorized Token-2022 donation PDA creation succeeded, but the crank pins legacy SPL Token and default ATA handling. Surfpool failed with `IncorrectProgramId` before Relay settlement.

**Reproduction:** Create a donation PDA for an approved Token-2022 quote, accrue fees, and invoke the crank.

**Remediation:** Use `TokenInterface` consistently for mint validation, ATA derivation, and the forwarded token program. Test legacy and Token-2022 donations end to end.

```rust
pub token_program: Interface<'info, TokenInterface>,
// Derive ATA with token_program.key() and forward that same program.
```

***

# Donation Relay

## Whitelisted transfer-fee tokens underfund settlement

**Final score: Medium — Likelihood: Medium; Impact: Medium.**

Donation records net input, but settlement records a gross transfer obligation. A 10% fee turned net 900,000 donation into 810,000 distribution funds, so the exact 900,000-input stub swap failed insufficient funds. The non-swap output route is fixed to USDT/SETTLEMENT and is not the affected path.

**Reproduction:** Relayer-whitelist a transfer-fee mint, donate a net amount, close the epoch, and invoke the swap route. Account for any top-up in net received units and handle withheld-fee cleanup separately.

**Remediation:** Reject fee-bearing mints regardless of whitelist, or record received deltas throughout and handle withheld cleanup.

```rust
validate_no_transfer_fee(&mint)?; // Apply even when whitelisted.
```

## Pausable Token-2022 mints pass the safe-mint check

**Final score: Medium — Likelihood: Medium; Impact: Medium.**

The safe-mint check omits PausableConfig. A signed non-whitelisted pausable-mint donation and independent pause committed; simulated close failed Token-2022 custom error 67. A funded accepted mint and independent pause authority are required.

**Reproduction:** Donate a pausable mint, have its independent pause authority pause transfers, then close or swap the affected epoch.

**Remediation:** Reject the extension or validate pause authority/state before whitelist checks. Test donation → pause → close and post-close pause → swap.

```rust
require!(extension::<PausableConfig>(&mint).is_err(), ErrorCode::PausableMint);
```

## Pre-created deterministic ATAs block epoch closure

**Final score: Medium — Likelihood: High; Impact: Medium.**

Anyone can pre-create an ATA for a PDA without its signature. Relay's `init` then fails `IllegalOwner`. Signed donation and outsider ATA precreation committed; simulated authorized close failed without state advancement.

**Reproduction:** Donate, pre-create the deterministic epoch-owned ATA as an outsider, then invoke authorized close. Repeat against each swap-output initialization site.

**Remediation:** Use `init_if_needed` for token ATAs while retaining mint/owner/program constraints; handle preexisting balances. Keep one-time state initialization strict.

```rust
#[account(
    init_if_needed,
    payer = payer,
    associated_token::mint = mint,
    associated_token::authority = epoch_pda,
    associated_token::token_program = token_program,
)]
```

## Whitelisted permanent delegates can drain donation vaults

**Final score: Medium — Likelihood: Medium; Impact: Medium.**

Whitelisting bypasses PermanentDelegate rejection. Signed whitelisted donation and signed independent delegate transfer of 1,000,000 units both committed. Relayer approval plus independent delegate control is required; other assets are unaffected.

**Reproduction:** Whitelist a mint retaining PermanentDelegate, donate it, then sign a delegate transfer from the donation vault without vault-owner authorization.

**Remediation:** Make custody checks non-bypassable and review existing accepted assets; removing whitelist status cannot revoke existing delegate rights.

```rust
validate_no_permanent_delegate(&mint)?; // Before any whitelist bypass.
```

## Unsolicited WSOL residuals freeze both swap routes

**Final score: Medium — Likelihood: High; Impact: Medium.**

After exact recorded WSOL input is swapped, Relay burns the residual; SPL Token rejects native Burn. Spending the entire balance instead violates exact-input accounting. The stub left 777 WSOL and residual burn failed custom error 10. This lifecycle can occur independently after a valid epoch close.

**Reproduction:** Add unsolicited WSOL, or lamports followed by SyncNative, to the debouncer before settlement. Swap exact recorded input and observe native residual Burn failure on both routes.

**Remediation:** Never burn native input. Synchronize and swap actual balance or handle surplus under an explicit ownership policy. Test both deposit methods, both routes, stale quotes, rollback, and conservation.

```rust
if mint != NATIVE_MINT {
    burn_residual(...)?;
} else {
    sync_native(...)?;
    settle_actual_native_balance(...)?;
}
```

