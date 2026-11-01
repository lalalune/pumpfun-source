# On-Chain Contract Security Review

**Date:** 2026-10-30  
**Repository:** `lalalune-source`  
**Release assessment:** **DO NOT DEPLOY this snapshot.** Two HIGH findings remain, and complete program builds are blocked. No CRITICAL exploit was confirmed; that is not evidence that critical vulnerabilities are absent.

## Scope and method

The review covered all five programs: Lalalune Main, LalaluneSwap / AMM, Fees, Donation Relay, and Mayhem. Scope included local support crates, instruction dispatch, account/PDA/signer checks, CPI boundaries, token and native value flows, arithmetic, configuration, migrations, and incentives.

Findings apply to the reviewed source and have not been fixed. Focused tests execute production helpers or extracted source functions; they do not establish full Solana transaction or deployed-program behavior. Program compilation failures prevent end-to-end exploit execution.

## Severity and finding summary

CRITICAL means a demonstrated permissionless, broad asset-loss or takeover path without a narrow setup assumption. HIGH covers serious asset loss, administrative takeover, or locked funds with explicit prerequisites. MEDIUM covers bounded value loss or material feature failure; LOW covers narrow configuration, operational, or defensive weaknesses. Likelihood, reachability, affected assets, and authority requirements determine the grade; severity is not raised merely because a theoretical outcome sounds severe.

| Severity | Count |
|---|---:|
| LOW | 14 |
| MEDIUM | 14 |
| HIGH | 2 |
| CRITICAL | 0 confirmed |
| **Total active findings** | **30** |

Findings are ordered from LOW to CRITICAL, followed by release priorities and build limitations.

---

# LOW

## L-01 — Lalalune creator migration accepts inactive sharing configurations

**Contract:** Lalalune Main  
**Locations:**

- `programs/lalalune/src/creator/migrate_bonding_curve_creator.rs:4-7,46-55`
- `programs/lalalune/src/creator/distribute_creator_fees.rs:241-256`
- `programs/lalalune/src/creator/distribute_creator_fee_v2.rs:203-220`

**Description:** `migrate_bonding_curve_creator` checks that the sharing-config admin matches the current creator, but does not require `sharing_config.status == Active` before assigning the sharing config as the curve creator. Both creator-fee distribution implementations subsequently reject inactive configurations.

**Failure path:** Once a matching inactive sharing config exists, any caller can invoke the permissionless migration. Future creator fees are routed to that config while ordinary distribution rejects it.

**Impact:** Creator-fee collection and distribution can become unavailable until the configuration is reactivated or privileged recovery occurs.

**Recommendation:** Require an active sharing configuration before migration. Consider requiring the sharing-config admin or another authorized signer for this irreversible creator-routing change, and add inactive/closed-config regression tests.

## L-02 — Main and AMM creator-fee maxima lack a 10,000-bps safety bound

**Contracts:** Lalalune Main / AMM  
**Locations:**

- `programs/lalalune-amm/src/instructions/admin/update_creator_fee_config.rs:9-10`
- `programs/lalalune-amm/src/instructions/admin/admin_cto_pool.rs:96-115`
- `programs/lalalune/src/lib.rs:153-155`
- `programs/lalalune/src/create_v2.rs:772-780`
- `programs/lalalune/src/creator/admin_cto.rs:326-338`
- `programs/lalalune/src/sell_v2.rs:341-368`
- `programs/lalalune/src/trade_v3.rs:1140-1148`

**Description:** The administrative setter accepts any `u64` value for `max_configurable_creator_fee_bps`. Creation and CTO enforce only that the selected fee does not exceed this configurable maximum; neither layer independently caps the fee at 10,000 bps.

**Failure path:** A global authority sets the maximum above 10,000 bps and creates or updates a controlled curve with a creator fee above 100%. Sells subtract protocol and creator fees from gross quote with checked subtraction, so excessive combined fees make sells fail. Buys can also charge disproportionate fees, subject to caller limits.

**Impact:** Administrative misconfiguration or a compromised global authority can disable sells and extract excessive trade value. This is not an unprivileged exploit.

**Recommendation:** Cap both the configured maximum and every selected creator fee at 10,000 bps. Enforce `protocol_fee_bps + creator_fee_bps <= 10_000` as a final trade-time invariant.

## L-03 — Main and AMM incentive schedulers accept nonpositive day lengths

**Contracts:** Lalalune Main / AMM  
**Locations:**

- `programs/lalalune-amm/src/state/volume_accumulator.rs:363-376`
- `programs/lalalune/src/token_incentives/volume_accumulator.rs:252-280,353-400,435-450`
- `programs/lalalune/src/incentives.rs:45-64`

**Description:** `update_schedule` stores `seconds_in_a_day` before conditionally validating the time range. An update with zero `start_time` and `end_time` can therefore set zero or negative day lengths. Zero causes day-index calculation to return no value; negative values can reach `usize::try_from(...).expect(...)` and panic.

**Failure path:** The global authority submits a schedule update with nonpositive `seconds_in_a_day` and zero time-range arguments. Subsequent rollover or claim operations stop accruing or abort.

**Impact:** Privileged misconfiguration can disable incentive accounting and claims in either program. On a fresh deployment, M-06 prevents creation of the prerequisite accumulator; this scheduler defect applies once that account exists.

**Recommendation:** Require `seconds_in_a_day > 0` unconditionally before storing it. Replace timestamp/day-length `expect` calls with checked, recoverable contract errors.

## L-04 — AMM pool creator migration accepts inactive sharing configurations

**Contract:** LalaluneSwap / AMM  
**Locations:**

- `programs/lalalune-amm/src/instructions/coin_creator/migrate_pool_coin_creator.rs:50-80`
- `programs/lalalune-amm/src/errors.rs:98-99`

**Description:** Pool creator migration assigns the supplied sharing config as `pool.coin_creator` after holder-reward and swept-fee checks, but does not validate its status. Account constraints verify the PDA, mint, and admin relationship only.

**Failure path:** If a matching config has `admin == pool.coin_creator`, any caller can migrate to it even when the config is inactive. The impact assumes the external fee program cannot distribute fees normally for an inactive config.

**Impact:** Future creator fees can become temporarily or permanently unclaimable and may require privileged creator reassignment to recover.

**Recommendation:** Deserialize the sharing config and require the intended active status before migration. Test inactive, closed, revoked, and otherwise invalid configurations.

## L-05 — Metadata-based AMM creator initialization trusts unverified creators and panics on an empty list

**Contract:** LalaluneSwap / AMM  
**Location:** `programs/lalalune-amm/src/instructions/coin_creator/set_coin_creator.rs:75-103`

**Description:** When metadata returns `Some(creators)`, the handler immediately indexes `creators[0]` and assigns that entry without checking its `verified` flag. The bonding-curve fallback is used only when the entire option is `None`, not when the list is empty or contains no acceptable creator.

**Failure path:** An empty creator list causes an out-of-bounds panic. If metadata is attacker-influenced, an unverified first entry can be assigned as the pool creator. Arbitrary users still need the relevant metadata authority to alter metadata.

**Impact:** Malformed immutable metadata can disable creator initialization and fee attribution; unverified metadata can misdirect future creator fees.

**Recommendation:** Use `creators.first()`, reject or fall back when no acceptable entry exists, and enforce the intended `verified` policy before assignment.

## L-06 — Users can close AMM accumulators with unclaimed incentive rights

**Contract:** LalaluneSwap / AMM  
**Locations:**

- `programs/lalalune-amm/src/instructions/token_incentives/mod.rs:13-16`
- `programs/lalalune-amm/src/instructions/token_incentives/close_user_volume_accumulator.rs:3-15`

**Description:** The close instruction returns rent to the user without checking `total_unclaimed_tokens` or unsettled `current_sol_volume`. Reinitialization creates zeroed reward accounting.

**Failure path:** The affected user must sign the close instruction, intentionally or without understanding that rewards remain pending.

**Impact:** The user permanently forfeits unclaimed incentive entitlement and unrolled volume. This finding does not claim theft of cashback tokens already held by an accumulator-owned ATA.

**Recommendation:** Require zero unclaimed tokens and zero unsettled volume before closing, or require an explicit destructive-force argument documenting forfeiture.

## L-07 — Empty fee-tier vectors cause an indexing panic in public fee queries

**Contract:** Fees  
**Locations:**

- `programs/lalalune-fees/lalalune-fees-math/src/lib.rs:48-53`
- `programs/lalalune-fees/src/lib.rs:174-176`
- `programs/lalalune-fees/src/types.rs:47-62`

**Description:** `select_fee_tier` unconditionally indexes `tiers[0]`. Public query paths call it without first requiring a nonempty vector. Normal tiers can be empty after initialization, and legacy decoding explicitly produces an empty stable-tier vector.

**Failure path:** A caller or downstream Lalalune/LalaluneSwap CPI selects a fee mode whose tier vector is empty. The query panics instead of returning a contract error.

**Impact:** Dependent trades and queries become unavailable until configuration is repaired. Direct invocation reverts only the caller's transaction; no direct asset-theft path was identified.

**Recommendation:** Make tier selection fallible using `tiers.first().ok_or(...)`, propagate a typed error through all query paths, and explicitly define any intended flat/normal-fee fallback for empty stable tiers.

## L-08 — One-step Fees authority rotation can permanently lock administration

**Contract:** Fees  
**Locations:**

- `programs/lalalune-fees/src/contexts.rs:121-129`
- `programs/lalalune-fees/src/lib.rs:167-171`
- `programs/lalalune-fees/src/instructions/admin/update_fee_program_global.rs:46-53`

**Description:** Fee-admin rotation accepts an arbitrary nonsigner key and explicitly permits the zero key. Global-authority rotation rejects zero but likewise requires no signature or acceptance from the new authority.

**Failure path:** The current authorized administrator makes a typo, is phished into selecting an incorrect address, or otherwise transfers control to an inaccessible key. There is no unprivileged escalation path.

**Impact:** Fee or global administration can be permanently locked, disabling tier updates, feature controls, claim administration, and other privileged recovery functions.

**Recommendation:** Implement two-step propose/accept authority rotation. At minimum, require a nonzero new-authority signer and reject the default key for both roles; consider multisig or timelocked administration.

## L-09 — Mayhem trade sizing contains avoidable panic paths

**Contract:** Mayhem  
**Locations:**

- `programs/mayhem/src/state.rs:310-323,361-400,477-492`
- `programs/mayhem/Cargo.toml:28-30`

**Description:** `retained_basis_points` performs `10000u16 - retained_bps` without first requiring `retained_bps <= 10_000`. Sell-sizing paths also construct a `Result` for invalid reserve arithmetic and immediately call `.unwrap()`.

**Failure path:** The configured trader supplies an excessive basis-point value, or a zero/insufficient reserve state reaches the unwrap. With release overflow checks enabled, these cases panic and revert rather than returning the intended typed error.

**Impact:** Instruction-level denial of service and unpredictable failure behavior for authorized trading. No persistent state corruption results because the transaction reverts.

**Recommendation:** Validate basis points before sizing, replace `unwrap()` with `?`, validate positive reserves, and return dedicated invalid-parameter or insufficient-reserve errors.

## L-10 — Main, AMM, and Mayhem one-step authority rotation can permanently lock control

**Contracts:** Lalalune Main / AMM / Mayhem  
**Locations:**

- `programs/mayhem/src/lib.rs:171-177`
- `programs/lalalune/src/global_init.rs:8-16` and `programs/lalalune/src/lib.rs:2986-2989`
- `programs/lalalune-amm/src/instructions/admin/update_admin.rs:3-8`

**Description:** Mayhem `update_admin`, AMM `update_admin`, and Main `update_global_authority` immediately write the supplied public key. The incoming authority need not sign or accept the role, and these paths do not reject the default key. Existing authority authorization is required.

**Failure path:** The current administrator accidentally selects an incorrect, inaccessible, or default key. The current admin signature is required, so this is an operational risk rather than an external privilege escalation.

**Impact:** Loss of administrative access can disable parameter updates, trader rotation, pause controls, and administrative withdrawals.

**Recommendation:** Add pending-admin nomination and signed acceptance, and reject the default public key.

## L-11 — Donation Relay swaps lack an independent minimum-output floor

**Contract:** Donation Relay  
**Locations:**

- `programs/donation-relay/src/cpi/jupiter.rs:6-19`
- `programs/donation-relay/src/settlement_handlers.rs:73-105`
- Equivalent alternative flow: `programs/donation-relay/src/handlers.rs:114-145`

**Description:** `swap_tokens` verifies exact input spend and only requires output delta to be greater than zero. Neither swap entrypoint accepts a protocol-level minimum settlement amount. The relayer-supplied Jupiter payload may contain its own slippage controls, but the relay does not independently enforce them.

**Failure path:** An honest relayer submits a route with absent, stale, or inadequate output protection. Adverse price movement or transaction ordering can produce a very small but nonzero output that passes relay validation. A fully malicious relayer already controls shares and recipients; this check primarily protects against honest misconfiguration and adverse execution.

**Impact:** Avoidable loss of settlement value for all recipients of an epoch.

**Recommendation:** Add `min_output_amount` to both swap entrypoints and enforce it after observing output. Keep Jupiter's route-level slippage controls as a second layer.

## L-12 — Donation Relay strands or burns unsolicited token credits inconsistently

**Contract:** Donation Relay  
**Locations:**

- `programs/donation-relay/src/tools/donate/shared.rs:44-54`
- `programs/donation-relay/src/settlement_handlers.rs:22-34,50-51,68-69,86-87`
- `programs/donation-relay/src/tools/distribution/shared.rs:124-128`

**Description:** Direct token credits to the debouncer ATA do not increase `debouncer.total_amount`, so epoch close leaves them stranded. In contrast, distribution and post-swap settlement distribute only accounted totals and then burn the entire residual vault balance before closing it.

**Failure path:** Anyone can transfer tokens directly to the publicly derivable ATAs. Debouncer credits remain untracked across epochs; extra distribution/output credits are destroyed during settlement. This does not redirect the already accounted epoch principal.

**Impact:** Unexpected loss or permanent unavailability of unsolicited credits, with inconsistent treatment between vaults.

**Recommendation:** Define and document one residual-asset policy: explicitly reject unsupported direct transfers operationally, include actual balances in accounting, or add a governed residual-recovery path rather than silently stranding or burning balances.

## L-13 — Untracked migration seed donations alter the initial AMM price

**Contracts:** Lalalune Main → AMM  
**Locations:**

- `programs/lalalune/src/migrate.rs:255-261,284-290`
- `programs/lalalune/src/migrate_v2.rs:257-261,308-327,340-343`

**Description:** Both migrations include the entire resulting base ATA balance in initial liquidity. A third party can pre-fund the canonical pool-authority base ATA; the seed amount then includes those donated tokens. V2 correctly measures the quote-side received delta but not the base-side delta.

**Impact and limits:** The donor can disturb the initial price and violate a policy that migration should seed exactly the curve's accounted amounts. The old report's claim of extracting migration quote liquidity was not established: adding base lowers price, and the ordinary arbitrage buys base while adding quote to the pool. In a fee-free constant-product model with reserves `B,Q`, fair price `Q/B`, and donation `D`, arbitrage does not recover the donor's full marked-to-market donation cost. No profitable attacker round trip or critical drain was demonstrated.

**Recommendation:** If donations must not affect seed sizing, derive the canonical base amount from accounted state/supply and measure actual transfer receipt, with an explicit residual-token policy. Handle donations to both the curve vault and the temporary ATA; fixing only the temporary ATA delta is insufficient. Otherwise document that migration intentionally includes unsolicited seed balances. See the economic witness in the main audit notes.

## L-14 — Fees funding accounts are readonly in generated instruction metadata

**Contract:** Fees  
**Locations:**

- `programs/lalalune-fees/src/contexts.rs:8-15`
- `programs/lalalune-fees/src/instructions/admin/extend_fee_config.rs:70-75`
- `programs/lalalune-fees/src/social.rs:119-132`

**Description:** `ExtendFeeConfig.user` is a signer without `mut`, although account extension debits it for rent. `ClaimSocialFeePdaV2.social_claim_authority` is likewise readonly although the token branch can use it to fund recipient ATA creation. Generated client/CPI account metadata therefore omits writable permission required by those funding operations.

**Impact:** Otherwise valid extension or ATA-creating claims built with default generated metadata can fail writable-privilege checks. Manually supplying writable metadata can avoid the failure. This is an integration availability defect, not an authority bypass.

**Recommendation:** Mark both funding accounts mutable, regenerate instruction metadata, and test extension/claim where additional rent or recipient ATA creation is actually needed.

---

# MEDIUM

## M-01 — Lalalune multi-hop completion fallback charges the full budget instead of exact completion cost

**Contract:** Lalalune Main  
**Location:** `programs/lalalune/src/multi_hop_curve_swap.rs:289-308,576-605`

**Description:** `complete_fill` computes the exact quote required to buy all remaining real tokens, but returns `None` when no usable post-completion fill exists. The caller then falls back to `(reserves, q, nf, None)`, where `q` and fees derive from the original full budget rather than the exact completion quote.

**Failure path:** A multi-hop buy crosses the real-token boundary but leaves insufficient budget for a nonzero post-completion fill. For example, with no fees, virtual token reserves of 1000, virtual quote reserves of 100, and real token reserves of 100, exact completion costs 12 quote units. A budget of 13 enters the crossing branch and the fallback purchases the same tokens for 13.

**Impact:** Direct trader overpayment. Excess quote is credited to curve reserves and migration liquidity; fee-bearing routes can also overcharge protocol and creator fees relative to actual completion cost.

**Recommendation:** When `complete_fill` returns `None`, recompute the exact completion quote, protocol/creator fees, total required input, and transfer-fee gross-up. Execute only that completion fill or reject the route if a post-completion component is mandatory.

## M-02 — Lalalune trading never records incentive volume

**Contract:** Lalalune Main  
**Locations:**

- `programs/lalalune/src/token_incentives/claim_token_incentives.rs:55-62`
- `programs/lalalune/src/token_incentives/volume_accumulator.rs:199-223`
- `programs/lalalune/src/lib.rs:360,716,768-805`
- `programs/lalalune/src/buy.rs:9-14,163,253-290`
- `programs/lalalune/src/buy_v2.rs:179-180,505,520-546,1000-1016`
- `programs/lalalune/src/trade_v3.rs:770-845,872-1005`

**Description:** The shared volume worker is the only code that adds trading volume to global and user accumulators. Its only call is in the claim path with zero new volume. Legacy buy's `track_volume` parameter is copied into events, while v2/v3 read and emit accumulator snapshots without calling the worker.

**Failure path:** The global authority schedules positive incentives and users trade, but neither global daily volume nor user current volume increases. Rollover produces no claimable rewards.

**Impact:** Newly scheduled rewards become unclaimable through Lalalune Main and funded incentive tokens can remain locked. The data flow is confirmed in source; if incentives were intentionally retired in the deployed version, this is a deprecated-functionality/recovery issue rather than a live rewards defect.

**Recommendation:** Invoke the volume worker from every intended eligible trade with actual protocol-defined SOL volume and correct `track_volume` semantics. If incentives are deprecated, disable scheduling and add an explicit funded-vault recovery path.

## M-03 — AMM trading never records incentive volume

**Contract:** LalaluneSwap / AMM  
**Locations:**

- `programs/lalalune-amm/src/state/volume_accumulator.rs:148-166`
- `programs/lalalune-amm/src/instructions/token_incentives/claim.rs:97-103`
- `programs/lalalune-amm/src/instructions/swap/buy.rs:279-284,469-473,618-623,839-843`
- `programs/lalalune-amm/src/instructions/swap/trade_v2.rs:929,1102-1105`
- `programs/lalalune-amm/src/instructions/swap/multi_hop_swap.rs:389-390`

**Description:** The only call to the volume-update function is the claim path with `sol_volume = 0`. Legacy buy's `track_volume` argument only reaches events, v2 and multi-hop initialize/read accumulator fields without updating them, and no sell path records volume.

**Failure path:** Users trade with tracking enabled, but global and user volume remain zero. Daily rollover cannot calculate rewards.

**Impact:** Token incentives are nonfunctional and deposited reward tokens can remain locked. Emitted fields can misleadingly suggest that volume was tracked.

**Recommendation:** Update both accumulators from every intended buy/sell path using actual SOL volume before emitting events. Add end-to-end tests proving that trades produce later-claimable rewards.

## M-06 — Main and AMM cannot initialize required global volume accumulators

**Contracts:** Lalalune Main / AMM  
**Locations:**

- `programs/lalalune/src/incentives.rs:12-27`
- `programs/lalalune/src/lib.rs:2889`
- `programs/lalalune/src/buy_v2.rs:158-160`
- `programs/lalalune-amm/src/instructions/admin/admin_update_token_incentives.rs:13-25`
- `programs/lalalune-amm/src/instructions/swap/buy.rs:167-170`

**Description:** Both programs' incentive updates require an existing owned global-volume PDA. Only the incentive token ATA is initialized; no exposed instruction initializes the global-volume account itself. Main legacy/v2 buys and AMM legacy buys require this account before their handlers run.

**Failure path:** A fresh deployment has no pre-existing accumulator. Creating a system account at the PDA cannot satisfy the program-owner and discriminator checks. The supplied instructions cannot bootstrap it, so affected buys and incentive configuration fail account validation.

**Impact:** Material launch functionality is unavailable on a fresh deployment. Pre-existing initialized accounts can mask the problem. This does not establish that every newer trade endpoint is blocked.

**Recommendation:** Add an authorized initializer for each accumulator with validated schedule, correct space/rent, and explicit initial state; test a fresh deployment through trading and reward claims.

## M-07 — Stable-fee updates can succeed but remain invisible on legacy-sized FeeConfig accounts

**Contract:** Fees  
**Locations:**

- `programs/lalalune-fees/src/types.rs:47-53,78-83,165-170`
- `programs/lalalune-fees/src/lib.rs:111-120,174-176`
- `programs/lalalune-fees/src/instructions/admin/initialize_fee_config.rs:10-12`

**Description:** FeeConfig decoding selects a layout from allocated account length rather than an explicit version. Legacy decoding discards stable-tier fields. Stable-tier updates serialize the complete struct and emit success events but neither resize the account nor require prior extension.

**Failure path:** An admin updates stable tiers while the account remains below the extended-layout threshold. If serialization fits, the instruction succeeds, but the next deserialization uses `read_legacy` and returns an empty stable-tier vector. A later normal-tier update can serialize that default and erase the stable configuration.

**Impact:** Configuration updates appear successful but are not honored by fee queries, potentially causing wrong fee selection or downstream availability failures. There is no unprivileged exploitation path; the sequence uses accepted administrative instructions and is generally recoverable by extending and reapplying configuration.

**Recommendation:** Require the extended layout before stable-tier updates or resize/fund within those instructions. Prefer an explicit layout version over allocation-length inference.

## M-08 — Native Mayhem LalaluneSwap trades mix closed-ATA rent with trade proceeds

**Contract:** Mayhem  
**Locations:**

- `programs/mayhem/src/instructions/buy_lalalune_swap.rs:25-26,101-120`
- `programs/mayhem/src/instructions/sell_lalalune_swap.rs:25-26,76-84`
- `programs/mayhem/src/instructions/lalalune_amm_interface.rs:399-405,593-597`
- `programs/mayhem/src/state.rs:230-251,600-606`

**Description:** Native buy/sell flows close the trader-funded WSOL ATA into `sol_vault`, then infer quote spent or gained from the vault's total lamport delta. Closing an ATA returns rent and other non-token lamports in addition to trade value.

**Failure path:** If `R` is the returned non-token lamport balance and `Q` actual trade value, buys record `Q - R` and sells record `Q + R`. Risk counters therefore understate buy exposure and overstate sale proceeds. An authorized malicious trader can repeatedly pay rent to manufacture risk-limit headroom. Small buys with `Q < R` underflow and revert.

**Impact:** Circumvention of global/per-coin risk controls, inaccurate events/accounting, and denial of otherwise valid small native buys. Only the configured trader reaches these paths; no unauthenticated theft was demonstrated.

**Recommendation:** Measure WSOL token balances before closing the ATA, or explicitly subtract non-token lamport refunds from vault deltas. Separate rent lifecycle accounting from risk accounting and use checked errors.

## M-09 — Donation tip multiplication overflows for otherwise valid amounts

**Contract:** Donation Relay  
**Locations:**

- `programs/donation-relay/src/tools/donate/shared.rs:44-54`
- Equivalent alternative flow: `programs/donation-relay/src/handlers.rs:34-42`

**Description:** The tip is calculated as `delta.checked_mul(tip_bps) / 10_000` entirely in `u64`. The intermediate product can overflow even though `tip_bps <= 10_000` guarantees the final tip is at most `delta` and mathematically fits.

**Failure path:** Any valid donation with `delta × tip_bps > u64::MAX` returns `ArithmeticOverflow`. For example, `delta = 10^18` and `tip_bps = 100` produces an intermediate `10^20`, above `u64::MAX`, although the correct 1% tip fits in `u64`.

**Impact:** Denial of otherwise valid donations, particularly for high-decimal tokens. The transfer and error are atomic, so no partial donation or direct fund loss occurs.

**Recommendation:** Perform multiplication and division in `u128`, then narrow the final tip with checked conversion. Add boundary tests immediately above `u64::MAX / tip_bps` and at 10,000 bps.

## M-10 — Legacy Mayhem trades derive Lalalune's bonding_curve_v2 PDA under the wrong program

**Contracts:** Mayhem → Lalalune Main  
**Locations:**

- `programs/mayhem/src/instructions/buy.rs:47-50`
- `programs/mayhem/src/instructions/sell.rs:39-42`
- `programs/mayhem/src/instructions/lalalune_interface.rs:308-310,420-436`
- `programs/lalalune/src/sell.rs:125-134`
- `programs/lalalune/src/buy.rs:166-167`
- `programs/lalalune/src/lib.rs:732-733,1040`

**Description:** Mayhem derives `bonding_curve_v2` without `seeds::program`, so the PDA is derived under Mayhem's program ID, then forwards it as the first remaining account. Lalalune independently expects the same seed derived under Lalalune's program ID and rejects any other address when creator fee is nonzero.

**Failure path:** A legacy Mayhem buy or sell reaches Lalalune while the applicable fee configuration produces `creator_fee != 0` and the trade is not fee-exempt. Lalalune returns `InvalidBondingCurveV2`, rolling back the complete trade.

**Impact:** Affected legacy Mayhem trades are unavailable whenever creator fees apply. No theft path was identified.

**Recommendation:** Derive the account with `seeds::program = LALALUNE_ID` and pass the canonical Lalalune PDA. Add legacy buy/sell CPI tests with nonzero creator fees.

## M-11 — Mayhem LalaluneSwap adapters omit the AMM's required pool-v2 account

**Contracts:** Mayhem → LalaluneSwap / AMM  
**Locations:**

- `programs/mayhem/src/instructions/buy_lalalune_swap.rs:64-69,109`
- `programs/mayhem/src/instructions/sell_lalalune_swap.rs:60-65,78-79`
- `programs/lalalune-amm/src/instructions/swap/buy.rs:451-461,822`
- `programs/lalalune-amm/src/instructions/swap/sell.rs:245,254-264,515-527`

**Description:** Mayhem defines `pool_v2` under its own program ID and does not forward it. Its remaining accounts contain only buyback recipient and ATA. For non-cashback trades with nonzero creator fees, the AMM expects canonical AMM-derived `pool-v2` at remaining index 0 and buyback accounts afterward.

**Failure path:** A Mayhem LalaluneSwap buy or sell targets a non-cashback pool with nonzero creator fee. The AMM interprets the buyback recipient as `pool-v2` and returns `InvalidPoolV2`.

**Impact:** Affected Mayhem AMM trades roll back and are unavailable.

**Recommendation:** Derive `pool_v2` with `seeds::program = AMM_ID` and prepend it to both remaining-account lists, followed by the two buyback accounts. Test both trade directions with nonzero creator fees.

## M-12 — Token-2022 quote donations cannot be cranked through Fees

**Contracts:** Lalalune Main / LalaluneSwap / Fees → Donation Relay  
**Locations:**

- `programs/lalalune/src/create_v2.rs:196-260`
- `programs/lalalune-amm/src/instructions/create_pool.rs:29-49`
- `programs/lalalune-fees/src/instructions/fee_sharing/create_donation_fee_pda.rs:111-184,242-249`
- `programs/lalalune-fees/src/donation.rs:152-165`
- `programs/lalalune-fees/src/lib.rs:247-248`
- `programs/donation-relay/src/instructions/v1/public_api/donate/donate_pubkey_config_id_with_payer.rs:22-41`

**Description:** Lalalune and AMM accept Token-2022 quote mints, and donation PDA creation records the quote mint without restricting its token program. The Fees crank instead hard-pins legacy SPL Token and a legacy TokenAccount ATA, then forwards that fixed program to the relay, although the relay supports TokenInterface and Token-2022.

**Failure path:** A donation PDA is created for a curve or canonical migrated pool with a Token-2022 quote mint. Accumulated quote fees reside in a Token-2022 ATA, but every crank fails the legacy token-program/ATA constraints before reaching the relay.

**Impact:** Donation flow is permanently unavailable for that PDA, and accumulated Token-2022 quote fees are stranded through the provided donation instructions.

**Recommendation:** Use `Interface<TokenInterface>` and `InterfaceAccount<TokenAccount>` in the crank, constrain mint/ATA to the supplied token program, and forward that program to the relay. Add an end-to-end Token-2022 quote-fee crank test.

## M-13 — Donation Relay accepts pausable Token-2022 mints as safe

**Contract:** Donation Relay  
**Locations:**

- `programs/donation-relay/src/tools/checks.rs:92-115`
- `programs/donation-relay/src/tools/donate/shared.rs:59-66`
- `programs/donation-relay/src/settlement_handlers.rs:22-34,55-105`

**Description:** The non-whitelisted mint-safety check rejects active mint/freeze authorities and several unsafe extensions, but ignores `PausableConfig`. A mint with an active pause authority can therefore pass the safety gate without relayer whitelisting.

**Failure path:** An issuer creates a pausable mint, revokes mint/freeze authority, and leaves transfers initially unpaused. Donations are accepted. The issuer later pauses the mint; transfer-checked CPIs used to close/settle the affected epoch fail. Other mints' epochs are not thereby frozen.

**Impact:** The issuer can deny settlement of donations of that mint until it unpauses. Attackers still need to induce donations of the affected asset; this does not freeze unrelated native or stablecoin donations.

**Validation:** A direct-source test executes the actual `typed_mint_safe` and confirms acceptance with active pause authority, then executes the pinned SPL Token-2022 processor and observes `MintPaused` on transfer. This is native processor execution, not a full Relay SVM transaction.

**Recommendation:** Reject active pause authority and paused state outside an explicitly documented trust policy. Prefer an extension allowlist and test every accepted extension's transfer, burn, and close lifecycle.

## M-14 — Creator-fee distribution overflows before dividing valid large payouts

**Contract:** Lalalune Main  
**Locations:**

- `programs/lalalune/src/creator/distribute_creator_fees.rs:148-165`
- `programs/lalalune/src/creator/distribute_creator_fee_v2.rs:163-168`

**Description:** Creator-fee splits calculate `balance.checked_mul(share_bps) / 10_000` in `u64`. The intermediate can overflow even when the final valid payout fits. The token path takes the entire source balance, so callers cannot simply choose a smaller withdrawal amount in this instruction.

**Failure path:** For a single 10,000-bps recipient, a balance above `u64::MAX / 10_000` fails. For example, `10^18` base units should produce a valid `10^18` payout, but intermediate multiplication returns Overflow. This can affect high-decimal quote tokens at substantially smaller human-readable amounts.

**Impact:** Valid creator-fee distributions revert and accumulated funds remain unavailable through the affected path until state/balance or implementation is changed. Native balances face the same arithmetic limitation at much larger practical SOL quantities. An unsolicited high-decimal token transfer can also push a previously working vault over the threshold; normal share updates that first distribute the old balance then fail as well. No transaction can partially pay recipients after a revert.

**Recommendation:** Widen multiplication and division to `u128`, narrow only the final amount, and regression-test high-decimal balances, full-share payouts, and the `u64::MAX / share_bps` boundary.

## M-15 — Whitelisted transfer-fee tokens leave Donation Relay epochs underfunded

**Contract:** Donation Relay  
**Locations:**

- `programs/donation-relay/src/tools/donate/shared.rs:28-63`
- `programs/donation-relay/src/settlement_handlers.rs:22-34,55-105`
- `programs/donation-relay/src/cpi/jupiter.rs:12-19`
- Equivalent alternative flow: `programs/donation-relay/src/handlers.rs:19-42,65-74,92-105,115-145`

**Description:** Donation accounting correctly records actual debouncer received deltas. However, whitelisted mints bypass mint-safety checks, including transfer-fee restrictions. Epoch close then records the debouncer's pre-transfer total as `distribution.total_amount` and transfers that gross amount without measuring the distribution ATA's received delta.

**Attack/failure path:**

1. The relayer whitelists a Token-2022 mint with a nonzero transfer fee, or a whitelisted fee-configurable mint later enables one.
2. Donations accumulate normally. For example, a 100-unit donation at 10% fee records 90 received.
3. Epoch close transfers 90 and records distribution total 90, but the distribution ATA receives only 81.
4. Non-swap settlement rejects 81 as below 90. Swap paths require exact input spend of 90, which the 81-unit vault cannot satisfy.
5. No contract-native reconciliation or recovery instruction supplies the missing principal. An external party can potentially subsidize the deficit through direct top-ups; withheld fees may also need harvesting before token-account closure.

**Impact:** Normal settlement of the entire affected epoch is blocked, requiring external subsidy/recovery or a program change. Do not interpret this as proof that no external recovery is possible. Severity is MEDIUM because this requires trusted whitelist admission, is isolated to that mint, and external recovery can be possible. A malicious issuer would first need whitelisting; ordinary donors need not be malicious.

**Recommendation:** Measure actual distribution ATA received delta during epoch close and store that amount as `DistributionV1.total_amount`, or reject transfer-fee mints even when whitelisted. Add an end-to-end nonzero-transfer-fee test covering donation, close, non-swap distribution, and both swap flows.

## M-16 — Permissionless foreign-mint claims can block a victim’s AMM cashback

**Contract:** AMM  
**Locations:**

- `programs/lalalune-amm/src/instructions/token_incentives/claim.rs:147-177,210-228`
- `programs/lalalune-amm/src/instructions/token_incentives/init_user_volume_accumulator.rs:9-22`
- `programs/lalalune-amm/src/state/volume_accumulator.rs:26-36`

**Description:** Cashback claims accept any token-interface mint and a nonsigning user. The caller can select an accumulator ATA for an attacker-created mint, but its entire raw token balance is added to one shared `u64 total_cashback_claimed`. No recognized-mint constraint or per-mint counter separates genuine cashback from unsolicited tokens.

**Attack path:** Read the victim’s counter `C`, mint `u64::MAX - C` units of a new plain SPL token, fund the victim-accumulator ATA, and create a receiving token account owned by the victim. A permissionless cashback claim sends the worthless tokens to the victim and raises the shared counter to `u64::MAX`. Every subsequent positive genuine cashback claim overflows; the transaction rolls back, retaining the genuine cashback in its vault.

**Impact:** Targeted, repeatable denial of cashback withdrawals without the victim’s signature. The victim can close and recreate the accumulator, but doing so resets history and can forfeit unclaimed incentive rights (L-06). This is recoverable griefing, not theft or destruction of all user funds.

**Validation:** Source checks confirm the nonsigning user, unrestricted mint, and account relationships; three tests execute the extracted production counter update and reproduce both zero-history and existing-history poisoning plus reset recovery. A full SPL mint/ATA/claim transaction has not been executed because the program build is blocked.

**Recommendation:** Bind claims to supported reward mints and keep counters per mint; do not let an informational aggregate counter prevent payout. A user signature helps prevent third-party poisoning but does not correct cross-mint arithmetic. Test unsolicited foreign-mint balances followed by genuine cashback claims.

---

# HIGH

## H-03 — Permissionless Mayhem global initialization permits administrative takeover

**Contract:** Mayhem  
**Locations:**

- `programs/mayhem/src/instructions/admin.rs:9-16`
- `programs/mayhem/src/lib.rs:45-79,124-126,171-224`

**Description:** `InitializeGlobalParams` accepts any mutable signer as `admin` and initializes the singleton `["global-params"]` PDA without a hardcoded expected administrator or deployment-authority constraint. The handler stores that caller as administrator. Later privileged instructions correctly enforce `has_one = admin`, but against the attacker-selected value.

**Attack path:**

1. The global-params PDA has not yet been initialized.
2. An attacker initializes it before the legitimate initializer and becomes `GlobalParams.admin`.
3. The attacker appoints itself as trader, changes risk/rate-limit parameters, pauses or resets state, and invokes native/quote withdrawals to its own accounts.

**Impact:** Complete administrative takeover and potential drainage of native and token assets held by Mayhem vaults. This is a deployment-time race; atomic legitimate deployment and initialization substantially reduces practical exposure, and takeover is not possible after proper initialization.

**Recommendation:** Restrict initialization to a hardcoded expected initial administrator or explicit deployment authority. Perform deployment and initialization atomically and verify admin/trader values before funding vaults.

## H-05 — Permissionless Main initialization permits launchpad administration takeover

**Contract:** Lalalune Main  
**Locations:**

- `programs/lalalune/src/lib.rs:93,2778-2794`
- `programs/lalalune/src/global_init.rs:3-5`
- `programs/lalalune/src/lib.rs:153-170,249-279`

**Description:** `Initialize` accepts any mutable user signer and creates the singleton `["global"]` PDA. The handler sets `global.authority = user`. No expected bootstrap key or deployment-authority check is present. Later admin instructions correctly enforce the stored authority, but the first caller chooses that authority.

**Attack path:** Before legitimate initialization, an attacker initializes the global PDA, then configures fee recipients, quote-mint policy, virtual reserves, migration settings, creator-management roles, and other global parameters. The intended administrator cannot run initialization again to regain control.

**Impact:** Complete launchpad administration takeover at deployment time, with future fee diversion and loss of launch configuration/control. This finding does not claim a post-initialization public drain of all existing curve reserves. It requires an uninitialized singleton and the opportunity to initialize first; a correctly initialized existing deployment is not vulnerable to this race.

**Validation:** Source trace covers the exported instruction, account constraints, state assignment, and subsequent `has_one` checks. The Global serialization size matches its allocation, avoiding an apparent-but-unreachable initializer claim. Full transaction reproduction is blocked by the build failures below.

**Recommendation:** Restrict initialization to an explicitly authenticated deployment/bootstrap authority. Initialize before public availability/funding, verify all roles, and use two-step authority rotation. Treat atomic controlled initialization as an operational mitigation, not a substitute for authenticating the initializer.

---

# CRITICAL

**No CRITICAL exploit was confirmed.** This is a bounded conclusion about the reviewed source and tests. It does not certify absence of critical vulnerabilities or make a non-building snapshot safe to deploy.

## Production build and validation blockers

| Component | Observed result | Consequence |
|---|---|---|
| Main | `cargo check` fails: missing CPI IDLs at `src/lib.rs:83-85`, plus invalid base58 quote-mint literal at `src/create_v2.rs:5` | No deployable Main artifact or full instruction tests established |
| AMM | `cargo test --lib` fails: missing IDLs at `src/lib.rs:22-23` | No full AMM instruction tests established |
| Fees | Root workspace test fails: missing IDLs at `src/lib.rs:27-28`, stable-only toolchain incompatibility and a try-block result-type error | Restore interfaces and an explicit supported toolchain before integration tests |
| Mayhem | Requires nightly Cargo; complete build remains unverified | No complete Mayhem build established |
| Donation Relay | Host execution is intentionally disabled; attempted default SBF build failed dependency resolution before compiling program source | Relay SBF build remains unverified; the environment failure is not labeled a program vulnerability |
| Workspace | Root `Cargo.toml` includes only Fees and fee math; remaining programs have independent workspaces. No lockfiles are included | A root workspace command does not validate all five programs; dependency resolution is not reproducible from the current snapshot alone |

The snapshot also hardcodes program and bootstrap-authority addresses. Their ownership and suitability for a new deployment were not verified; replacing names does not establish control of those addresses. A fresh deployment test must demonstrate initialization under the intended keys and correct CPI IDs.

## Evidence and tests

Focused tests cover real token-extension/native-fee helpers, malformed parsing inputs, pausable-mint admission and actual SPL rejection, distribution conservation, Mayhem accounting/panics, and source/model checks of Main findings. A passing witness often means it successfully reproduces an existing bug; it is not a remediation pass.

Full cross-program Solana transaction tests, compute/stack limits, deployed-program equivalence, and economic fuzzing were not established. Missing IDLs, unresolved dependencies, and build errors prevent stronger conclusions. No deployment or chain transaction was performed.

## Remediation priority

1. Fix **H-03 and H-05** before exposing or funding a fresh deployment: authenticate the first initializer and verify all resulting authorities.
2. Restore reproducible builds for every program, then fix **M-06** so fresh installations can initialize required state and execute buys.
3. Fix **M-12 through M-16** before accepting affected token donations or creator fees; enforce mint policy across the full lifecycle.
4. Fix remaining accounting, configuration, and client-metadata findings; add negative authorization, balance-conservation, token-extension, migration, and fresh-state integration tests.
5. Re-audit the repaired, pinned source and generated binaries before release. Existing admin checks, arithmetic helpers, and fixed CPI IDs are useful controls, but do not substitute for these missing execution checks.

Framework semantics were checked against the pinned dependency source and the primary [Anchor account constraints documentation](https://www.anchor-lang.com/docs/references/account-constraints). Solana program context: [official program documentation](https://solana.com/docs/core/programs). Findings themselves are grounded in the local source references above.
