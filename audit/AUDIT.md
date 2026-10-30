# Consolidated security assessment

> `repro/` was removed from `main` in `fce9f28d` and the rest of `audit/` in `b4448f7b`;
> the `../repro/...` and `pump*/...` links below are historical and resolve at those
> commits' parents.

**Status: incomplete; not a security sign-off.** Scope is the four captured original
programs listed in `docs/SCOPE.md`. Partial executable handlers have been recovered; no complete program exists.

The current published recovery covers 140 implemented handlers plus five partial
Pump paths and 53,787 saved comparison receipts: [Pump48 decoder/preparation checkpoint](../repro/pump/curve-preparation-fortyeight/README.md),
[AMM37 accumulator-order checkpoint](../repro/pump_amm/accumulator-order-v144/README.md),
[Fees31 V2 caller checkpoint](../repro/pump_fees/v2-caller-v144/README.md),
and [Mayhem24](../repro/mayhem/twentyfour/README.md). These bounded recovery results
do not extend the source review frozen at commit329fc44 into a complete audit of
the later candidates. All four original whole-file comparisons still differ.
The local [sell_v2 transfer-fee correction](../repro/pump/sell-v2-transfer-fee-20261026/README.md)
now matches the original in the 206-case handler corpus, including 22 new fee
cases, and has a reproduced current-source build. This does not extend the
historical security review or establish whole-program byte identity.
Mayhem's only remaining identified handler is initialize_mayhem_state; its
initializer work remains stopped. Historical checkpoints below retain their
original counts and scope.

| Severity | Confirmed findings |
| --- | ---: |
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |

There are no substantiated vulnerability findings in this checkpoint. No hypothetical
issue is presented as a finding, and no informational findings are included.

## Public candidate-source review progress

The [fourth layered pass](../repro/layered-passes/pass-04/README.md) reviews the
accepted source frozen at `aa98fb45f3f756d008ccb9940bcfd9a6e986ef77`. Each package
records exact per-file, per-function and account-context coverage:

| Candidate | Inspected explicit functions | Inspected account contexts | Review |
| --- | ---: | ---: | --- |
| Pump | 209 | 38 | [Report](../repro/layered-passes/pass-04/audit-pump/REPORT.md) |
| AMM | 117 | 30 | [Report](../repro/layered-passes/pass-04/audit-amm/REPORT.md) |
| Fees | 64 in-program definitions | 30 | [Report](../repro/layered-passes/pass-04/audit-fees/REPORT.md) |
| Mayhem | 61 | 15 | [Report](../repro/layered-passes/pass-04/audit-mayhem/REPORT.md) |

Fees separately inventories eight standalone definitions and two external
declarations. Pump retains six excluded declarations as opaque metadata. These
lexical inventories have explicit scope rules and are not percentages of audited
machine code. The reviews retain their qualified observations and establish no
new confirmed vulnerability or independently justified source patch. Their
verifiers check source provenance and coverage integrity, not all-state safety.
Generated code, transitive dependencies, lifecycle and alias premises, incomplete
reconstructions and excluded work still prevent security sign-off. This source
applicability does not transfer to subsequent reconstruction changes. The current
Fees legacy-caller change postdates this frozen review. The subsequent
[delta review](../repro/layered-passes/pass-05/audit-fees-delta/REPORT.md) checks
all 26 frozen inputs and 14 explicit functions in its changed module, finding
no concrete new regression. It retains F1–F5 and updates F5 for conditional
prepared payout; it does not close lifecycle, V2, generated-code or transitive
equivalence gaps. Source/build/regression evidence alone does not establish
complete security coverage.

The [third parallel pass](../repro/parallel-work/2026-10-25/results/README.md) contains new manual source reviews for the four candidates frozen at 517d77d. They enumerate 112 included Accounts contexts and 422 function declarations/dispositions, with explicit excluded boundary rows. Twenty-five candidate observations retain authorization, policy, reachability and dependency prerequisites; they are not confirmed vulnerabilities in the captured originals. The verifiers check provenance, spans and bounded calculations rather than certifying every review conclusion.

The later Fees state-module and SharingConfig-module changes preserve five complete account declarations and add reexports/module wiring. Its code-generation and regression evidence does not automatically extend the frozen review to every macro-generated behavior. Missing implementations, partial paths, excluded scopes, deployment evidence and transitive dependencies still prevent whole-program security sign-off. Private audit inputs remain unpublished.

## Local evidence and applicability

`audit/local-validation.json` records 393 deterministic, local LiteSVM transactions
using solders 0.27.1: 123 Pump, 105 PumpSwap, 98 Pump Fees and 67 Mayhem cases. All
were rejected. Inputs cover empty/short/unknown discriminators, 64 deterministic
random inputs per program, and each available official IDL discriminator with no
accounts or argument payload. Known discriminators reach instruction logs; failures
include missing accounts, argument decoding and explicitly disabled instructions.

This demonstrates basic dispatch and malformed-input rejection for those exact
inputs and captured hashes only. It does not test valid account substitution,
privileged signer constraints, successful trading, balances, token-extension edge
cases, economic invariants, rate limits, migrations, or cross-program calls.
That 393-case corpus does not exercise recognized Mayhem instruction paths because
the captured documentation has no official Mayhem IDL. Later bounded recovery
coverage is recorded separately. External programs are captured as dependencies
but are not security-audited here. No mainnet simulation, transaction submission,
exploit, or broadcast was performed.

The evidence verifier and six comparator mutation tests validate capture integrity
and ensure code/padding changes are not hidden by the comparison utility. They are
not evidence of on-chain program correctness. Source recovery, valid-state security
validation and complete audit coverage remain outstanding.

The recovered selector additionally matches 1,215 local original-program calls
using synthetic fee configurations (see `docs/FEE_SELECTION.md`). This includes
unsorted and duplicate thresholds but does not establish that such configurations
are reachable through authorized update instructions. Empty tiers panic in the
original; no vulnerability is asserted without establishing reachable state and
impact. These checks do not complete the broader audit.

## Imported lifecycle validation

The integrated lab adds 30 freshly replayed, signed transactions against the
captured original Pump, PumpSwap and Pump Fees programs in offline Surfpool 1.6.1.
Seven saved-evidence verifiers and seven fresh-evidence verifiers passed. Covered
paths include synthetic-authority config writes and rejected outsiders; fresh SOL
coin creation, v3 trades and completion; migrate_v2 with the two required remaining
accounts; v2 trading on captured and freshly migrated pools; and synthetic referral
vault withdrawal with signature/PDA/recipient rejection controls. Source provenance,
logs, exact receipts and limitations are under `research/`.

These results expand bounded valid-state coverage to ten distinct published
handlers (five Pump, three PumpSwap and two Fees). They do not establish real
authority control, live fee accrual, all quote/token modes, or behavior for Mayhem.
The tests use the captured core executables with the harness/runtime dependency
configuration; no whole external-dependency version equivalence is claimed. No
additional vulnerability finding or completed source audit follows from these
successful paths.

### Quote-mint fee routing

The recovered native router was compared with 9,428 local original-program
queries covering quote classification, schedule boundaries, exotic fee fallback,
and injected empty/unsorted schedules. No behavioral mismatch was observed.
See `docs/FEE_SELECTION.md` and the complete compressed differential receipt.
The two SBF compiler candidates still differ from the original router; this is
partial implementation evidence, not whole-program equivalence or completed
audit coverage. Empty-schedule panics in directly injected state are not a
confirmed vulnerability without a reachable configuration path.

### Executing recovered handlers

Pump Fees now has 31 independently compiled instruction bodies, with 17,461
original-versus-candidate SBF comparison receipts, including 69 baseline repeated-input checks and eight focused repeats. These cover two query handlers, four authority setters,
global initialization against the historical 740-byte Pump Global layout, and
three configuration setters, permissionless resize, and two deprecated rejection
dispatches, two tier upserts and FeeConfig administrator transfer, two donation handlers and three social-fee handlers and referral withdrawal, four buyback handlers, sharing creation, administrative sharing reset, both sharing updates and FeeConfig initialization. All31 bodies have bounded implementations; full source/context equivalence remains unproven. Selected compiler and dependency versions
remain candidates rather than an established historical graph.

### Historical reconstruction checkpoint: 111 implemented handlers and four partial paths

Saved builds cover Pump 30, PumpSwap 32, Pump Fees 31 and Mayhem 18 implemented
handlers, plus Pump's partial buy_v3, sell_v3, buy_exact_quote_in_v3 and create_v2 paths. Their 40,105 local SBF
comparisons were indexed by the then-current `repro/status.json`; each retained report preserves its own
coverage and limitations. Pump's SOL trade paths include Mayhem buyback suppression,
holder-reward event fields and explicit cashback rejection. USDC quote behavior adds 130 synthetic SPL/Token2022 cases; other quote routes
and the final event suffix remain incomplete. Neither is counted
as a fully recovered trade handler. See [partial sell review](pump/partial-sell-review.md).
The new legacy creation handler has bounded captured-Metaplex CPI coverage.
The partial create_v2 path covers normal SOL and holder-reward creation; Mayhem and
alternative quote creation remain unsupported in this candidate. Exact-quote v3
coverage uses SOL and synthetic USDC/Token2022 fixtures without extensions.
The combined Pump candidate passed 346 offline Surfpool comparisons with 692 signed
transactions; these receipts establish only their stated behavior and runtime scope.

PumpSwap deposit/withdraw coverage includes actual captured Token/Token2022 CPIs,
transfer-fee extension fixtures, slippage and exact inner instructions. See
[liquidity recovery](pump_amm/LIQUIDITY_RECOVERY.md). Mayhem coverage adds rent-funded
account extension and privileged SOL withdrawal with signed timestamp/rate-limit
arithmetic. Its permissionless recipient creation does not store a caller-chosen
beneficiary; downstream sweeps and other authorization paths remain under study.
Synthetic invalid states or permissionless instructions alone are not findings.

All four full-file comparisons still differ. Trading, liquidity, fee sharing,
claims, migrations, dependencies and hostile CPI/token-extension paths remain
incompletely reconstructed or audited. No complete audit conclusion follows from
these bounded tests. SPL Token has a fresh Linux source build matching all 108,600
captured bytes, preserved under `repro/pump/verified-spl-token/`; byte identity does
not establish security of that dependency or its callers.

Token2022 now also has a fresh pinned Linux source build matching the full capture
after explicit zero allocation padding. ATA and donation relay have no verified
source attribution in the latest saved registry response. Metaplex's registry
response points to a failed, mismatching Phoenix build; that repository is rejected
as source attribution. The failed registry records are retained separately and
do not establish that the correct source is unavailable.

### Versioned configuration and sweep coverage

Fee schedule updates reject empty schedules, more than 50 tiers, duplicate or
unsorted thresholds and fee totals above 10,000 basis points. Checked-add overflow
aborts and rolls state back. These authorized-update constraints narrow earlier
query observations involving injected empty/unsorted schedules; such injected
states alone do not establish an exploitable path. The decoder intentionally
ignores newer fields in legacy allocations. The configuration setter suite tests
migration boundaries and the exotic setter's resize/rent transfer behavior.

Mayhem's current compiled candidate covers quote withdrawal and both fee sweeps.
The added 1,021 cases include signer/role checks, rate limits, recipient duplicates,
token program substitutions, token ownership/mint errors and counter arithmetic.
They establish bounded agreement only. A separate privileged-PDA initialization
experiment was stopped by automated safety review and is not included in the
implemented-handler count, saved accepted coverage or any security conclusion.

The two deprecated Fees authority-sharing dispatches are counted only as observed
unconditional rejection behavior (6023), not successful authority changes. The
297-case permissionless resize suite compares owner/discriminator/stored-bump
checks, exact rent-delta transfers, no-op behavior, new zero-filled bytes and
rollback. Injecting an underfunded synthetic account can fail rent checks after
execution; that observation alone is not a vulnerability finding.

PumpSwap's three v2 trade handlers add 870 original/candidate cases covering
canonical and noncanonical pool fee selection, SOL/USDC/exotic quote schedules,
legacy account resizing, Token2022 transfer fees, exact token/System/event CPI
payloads and failure rollback. See [v2 trade recovery](pump_amm/TRADE_V2_RECOVERY.md)
for semantic details and untested extension combinations. The first-generation
trade handlers and multi-hop routes remain outside this recovered checkpoint.

AMM pool creation adds 283 signed comparisons, including calls through the original
Pump migration path with its actual PDA signer. Pool/LP/vault creation, locked LP
supply, existing vault balances, optional argument parsing and tested mint extension
checks agree. The later nineteenth-handler checkpoint adds `init_boost` and 100 cases, including
a complete committed non-Mayhem migration through the original Pump caller.
This validates that specific migration path, not all migration/boost behavior. See
[pool creation recovery](pump_amm/CREATE_POOL_RECOVERY.md).

The combined Fees executable now also passes the 713 donation creation/forwarding
fixtures. Creation validates canonical pool and creator/sharing authorization;
forwarding validates its stored-bump donation PDA, retains rent for 218 bytes,
wraps excess native SOL and calls the captured relay. Zero token balance returns
after ATA initialization. The relay amount, config, message, credited program,
account flags and signer seeds are compared. A persistent 10-step signed sequence
and 10 independent Surfpool comparisons also pass against the combined build.
No cooldown was observed at the tested same-time, one-second and one-day intervals;
this is an observed rule, not a vulnerability claim or complete timing audit.

Six additional Pump administrative handlers add 351 original/candidate cases:
quote whitelist add/remove, initial virtual quote reserves, buyback configuration,
creator-fee configuration and holder-reward configuration. The existing four
administration and partial-trade suites also pass against the same new executable.
Buyback basis points reject values above 10,000, whereas tested configurable
creator-fee maxima retain full u64 inputs. Only the creator-fee configuration
setter emits an event in these six recovered paths. These recovered permissions
and boundaries do not establish that every downstream use is safe.

Social-fee creation and both claim instructions add 1,562 signed original/candidate
comparisons and 29 independent Surfpool comparisons on the combined Fees build.
They cover authority checks, disabled flags, cooldown/no-balance returns, SOL rent
retention, saturating counters, token transfers, ATA creation and return/event
bytes. Event balances can reflect a saturating arithmetic calculation rather
than a reloaded token balance (including a synthetic self-transfer). That observed
event behavior alone does not establish a reachable financial loss. Separate
Surfpool processes normalize only decoded wall-clock timestamps and retain raw
values. Every new handler remains subject to the larger incomplete audit scope.

The next checkpoint adds signed referral withdrawal, two Pump authority/recipient
setters, and both AMM fee sweeps. Referral withdrawals retain native rent and check
optional token authority/mint/program constraints. AMM sweeps authenticate the
configured recipient or creator vault, validate fee balances and virtual-reserve
arithmetic, transfer the selected bucket and preserve the other bucket. The 254
sweep cases include captured Token2022 transfer-fee execution, but are not an
exhaustive extension or aliasing audit. Normal recipient lookup uses binary search;
injected unsorted arrays rejecting a present key are an observation, not a confirmed
reachable vulnerability. All original/candidate bytes remain independently compared.

The eighty-handler checkpoint adds Pump volume-account initialization/closure,
AMM raw account extension, four Fees buyback handlers and sharing creation.
Volume close accepts tested nonzero reward fields; raw AMM extension charges the
difference between old/new rent minima even for already overfunded accounts.
These are observed rules from synthetic states, not demonstrated vulnerabilities.
Buyback coverage includes signed rate-limit arithmetic, initialized zero authority,
rent retention, transfer order and counter overflow. Sharing creation uses genuine
captured Pump/AMM CPIs with their normal authority checks and PDA signing.

After moving the combined Fees candidate to platform-tools v1.44, all 16,851 SBF
cases, 81 Surfpool comparisons (162 signed transactions), and the ten-step donation
sequence passed again on that executable. The compiler selection follows exact
runtime helper-body comparisons, not complete binary equality. Full reconstruction,
state reachability analysis, exhaustive dependency/CPI coverage and security
assessment of all unrecovered handlers remain outstanding.

### All Fees instruction bodies and AMM creator-fee paths

Fees now has bounded implementations for all31 IDL instruction bodies, including
two deprecated rejecting dispatches. The combined executable passes17,361 SBF
comparisons and112 Surfpool comparisons. The final initializer uses two authentic,
unchanged historical signed messages, with signature verification enabled and only
blockhash freshness adapted for local replay. It creates the observed2,512-byte
FeeConfig; rent, zero defaults and events match the captured program and saved
historical metadata. This does not reproduce the entire historical bank or prove
equivalence of all initializer account combinations.

Sharing updates execute genuine Pump/AMM fee distribution before validating the
new shares, with rollback on failure. Administrative reset is reached through the
captured Pump caller signing its own PDA; some direct Fees context constraints
remain only indirectly tested. All31 bodies being present is therefore a recovery
milestone, not completed source reconstruction or a security sign-off.

AMM creator-fee collection and both transfer-to-Pump variants add415 cases. The
25-handler combined AMM candidate passes12,306 cases including prior regressions.
The source preserves tested native-rent thresholds, quote-token transfers, exact
CPI/event bytes and permission constraints. Dependency and lifecycle reachability
questions remain; full ELF equality is false for all four programs.

### Pump creator-fee integration

Four additional Pump handlers cover native creator-fee collection, distribution
v1/v2 and the minimum-distributable query. The combined candidate passes 1,924
SBF comparisons and 50 Surfpool comparisons with 100 normally signed offline
transactions. The package preserves frozen source, harnesses, fixtures and raw
receipts under `repro/pump/creator-eighteen/`. See
[creator-fee recovery](pump/creator-fees-recovery.md) for rent thresholds,
rounding, token paths and bounded coverage. This new source is outside the
independent static review frozen at commit `329fc44`; no security sign-off
is implied by its behavioral comparisons.

### PumpSwap creator reassignment

The combined 28-handler candidate adds creator migration, metadata/bonding-curve
creator selection and administrative CTO. All 12,792 saved cases across 17 suites
pass, including 327 direct reassignment cases and 159 CTO cases. Of the CTO cases,
140 reach AMM through genuine captured Pump CPI; 19 reject upstream. Normal
test-owned signatures remain verified. The captured Pump program supplies its own
PDA signature for CPI. See [recovery details](pump_amm/CREATOR_REASSIGNMENT_RECOVERY.md)
for ordering corrections, synthetic-state limits and exact build provenance. Ten
AMM IDL handlers remain absent. This addition is outside the source review frozen
at commit 329fc44 and does not complete the original-program security assessment.

### Historical Fees error-message checkpoint

That Fees build restores the complete 37-variant IDL error enum and the
literal `format` messages observed for errors 6003 and 6011. All prior 17,361 SBF
checks and two added error-message comparisons pass, for 17,363. The earlier
112 Surfpool comparisons refer to the retained pre-correction executable.
Source locations and compute logs still differ. This repairs reconstruction
fidelity and does not assert a vulnerability or complete source equivalence.

### Historical Mayhem burn and framework checkpoint

That eighteen-handler Mayhem build passes 2,953 inherited comparisons
and six genuine-snapshot burn instruction comparisons. Each of three first burns
succeeds; a second burn on the actual resulting local state rejects with 6004.
Normal signatures and blockhash checks remain enabled. Raw compute logs and
source-location strings differ and are retained. The candidate uses an Anchor
1.0.0 baseline with explicit System-ID validation to preserve the captured check
order. See [the package](../repro/mayhem/eighteen/README.md) for exact inputs and
limits. Seven identified paths remain absent; this is not historical replay or
a completed audit. The frozen source review at 329fc44 excludes this addition.


## Dependency and static-recovery checkpoint

Metaplex [candidate11](../repro/pump/metaplex-candidate-build-11/README.md) passes 135 inherited differential comparisons and matches 1,250 of 1,251 inferred function windows byte-for-byte. The final Utilize window and source-coordinate/relocation bytes still differ; the inherited cases do not exercise the corrected zero-use guards. This is reconstruction evidence, not a completed dependency audit or a claim of full behavioral equivalence.

The Pump [set_mayhem_virtual_params static package](../repro/pump/mayhem-virtual-params-static/README.md) has no compiled implementation or runtime receipts. Its required Mayhem sol-vault PDA signer lacks an established genuine invocation in this lane. Static provenance verification does not establish reachability or security, and contributes no handler or comparison count.


## Quote-control recovery checkpoint

[Pump48](../repro/pump/quote-control-fortyeight/README.md) adds the six quote-control handlers with 507 fresh signed comparisons. Its 800 failed executions preserve all nonpayer state and payer state except expected signature fees. All 8,654 earlier cases and 1,024 Surfpool comparisons were rerun against the new ELF. Root independently verified the package, current source bindings and saved signatures. These bounded results cover tested role restrictions, account growth, mint eligibility and event behavior; they do not establish a complete audit. The current sell_v2 transfer-fee gap and four partial paths remain unchanged.


## AMM Pool serialization fidelity

The [Pool serializer checkpoint](../repro/pump_amm/pool-serialization-thirty-seven/README.md) replaces two explicit error-string conversions with the original's observed direct I/O-error conversion. The complete 1,704-byte normalized Pool exit and all 24 direct callees now match; the earlier GlobalConfig match remains. All 25 existing suites / 17,462 comparisons pass freshly on the new ELF, and clean main and scratch builds are whole-file identical. This adds no handlers or unique test inputs and does not establish transitive data or original whole-file identity.


## Partial native curve execution through AMM

The [partial curve checkpoint](../repro/pump/native-curve-partial-fortyeight/README.md) adds one native/legacy curve per Pump CPI, using the captured AMM's genuine PDA signing. Its 56 comparisons include 50 that reach Pump, six AMM caller rejections and 11 successes; all 112 ordinary outer signatures were verified. All 9,161 previous Pump cases and 1,024 Surfpool comparisons pass on the new executable. Multiple curves, other endpoint flags, nested/non-native quotes, Token-2022, holder rewards and completion crossing remain unsupported. This is a fifth partial path, not an additional fully recovered handler. No complete security audit follows from these bounded results.


## Fees call/data closure limits

The [bounded update-admin closure](../repro/pump_fees/update-admin-call-closure-static/README.md) visits 59 body pairs: 58 normalized matches and 16 raw matches, with one unmatched FeeConfig account decoder wrapper. Sixteen bounded pointer/length spans match; indirect calls, depth limits and 133 data extents remain unresolved. Matching instruction bodies also reference different compiler/source-location records. [Official Linux/Darwin sysroot evidence](../repro/pump_fees/linux-v144-sysroot-provenance/PUBLICATION.md) explains one allocator-filename difference without rewriting it. These are source-fidelity observations, not new runtime coverage, a proved vulnerability or a completed transitive audit.

The [cached public Pubkey source attribution](../repro/pump_fees/pubkey-source-coordinate-attribution/README.md) identifies `solana-pubkey` 2.2.1 as a concrete candidate: both observed original source coordinates match, and four relevant source blocks equal the current 2.4.0 blocks. The surrounding source changes explain the shifted coordinates. This does not uniquely identify the historical version, dependency graph or build recipe, and no dependency change or new runtime claim is made.

The [decoder-contract review](../repro/pump_fees/decoder-contract-static/README.md) resolves the apparent discriminator-slice discrepancy: the three original body thresholds equal the candidate account thresholds after adding eight bytes, and both observed original callers discard their local cursors after decoding. Internal helper layout, allocation branches and error formatting still differ. This evidence does not justify a behavioral correction or prove full equivalence.

The donation-business checkpoint adds a grounded curve branch and diagnostic corrections, with20 focused comparisons (eight repeated inputs,twelve new typed combinations) and the unchanged17,441-case baseline. These are reconstruction checks, not a completed security review. Historical audit packages retain their original scope.

The [current Fees and AMM applicability reviews](../repro/parallel-work/2026-10-25/current-audit-results/README.md) pin published source `7a9cf01`. Fees retains all five observations and directly reviews the changed donation branch and context. AMM retains all nine observations, reviews the new initializer and shared setters, and distinguishes conditional current-source arguments from unresolved historical deployment and runtime premises. No new target execution, confirmed original vulnerability, or security sign-off follows. Root read both reports and independently passed their portable integrity and source-binding checks.


The [nested-ancestry checkpoint](../repro/pump/nested-ancestry-fortyeight/README.md) adds sixteen bounded original/candidate comparisons while preserving the complete prior Pump and Surfpool corpus. Synthetic pre-existing ancestry and finite depth/Pool cases do not establish exhaustive account admission, lifecycle reachability or complete source security. The newly integrated Pump source requires its own current-source applicability review; the Fees/AMM review above does not cover it.

The Pump decoder/preparation correction in [pass06](../repro/layered-passes/pass-06/README.md) postdates the frozen candidate-source reviews. Its exact source review, clean-build identity and unchanged regression evidence do not extend those audits into full security acceptance. The Relay owned-error build and uncompiled Fees proposals likewise retain separate source/build/runtime applicability. No new confirmed vulnerability finding or complete security assessment is asserted.

The seventh-pass Fees change affects one legacy error's compared-value payload. Its source review, retained-body checks and unchanged runtime corpus do not constitute an independent complete security audit. No new confirmed vulnerability finding is asserted, and the earlier frozen audit's applicability limits remain.

Pass08's independent review checks bounded original named-key provenance and documents unevaluated branch and padding assumptions. The unchanged Fees corpus and Relay ordinary12 comparisons are regression evidence, not a complete security audit or proof of all historical behavior. No new vulnerability finding is asserted.

Pass09 changes the AMM accumulator assignment order using original instruction evidence and retains unchanged runtime comparisons. It adds no new security finding or complete audit sign-off. Its dependency review distinguishes unresolved code/data and provenance differences from demonstrated behavioral faults.

Pass10's Pump fee-input and Mayhem typed-error changes have bounded independent source/static review and unchanged regression evidence. Pump divergent-supply runtime coverage is still absent; Mayhem diagnostic differences and missing raw administrative transaction bytes remain explicit. These reviews do not establish exhaustive behavior or complete the security audit.

Pass 11's two narrow source corrections passed unchanged corpora and independent source/operand review. These finite checks do not cover Pump's simultaneous complete/cashback flags or establish full Mayhem helper equivalence. The AMM formatting-source proposal is not security acceptance. The broader security assessment remains incomplete.

Pass 12 restores a supported dependency algorithm and its typed failure paths, with whole-window static checks and the unchanged AMM corpus. Normalized function matches do not prove full recursive data identity, exhaustive behavior or security acceptance. The full security audit remains incomplete.

Pass14 reviews the Relay IDL header error lifetime from I/O destruction through owned reporting/lowering. The unchanged ordinary corpus passes but does not validate every changed failure arm. No full original, historical-build or security-audit acceptance follows.

Pass15 restores observed optional-error conversion and account ownership/lifetimes. Finite corpus and full selected function matches do not establish full recursive data identity, untested error arms, or complete security acceptance. Known diagnostic gaps remain visible.

Pass16 adds fresh source-coverage reports for Pump, Fees, AMM and Mayhem under [security-reviews/pass-16](../repro/security-reviews/pass-16/README.md). The reports distinguish candidate-source consequences and conditional concerns from deployed behavior. AMM review binds the preceding context checkpoint; its sole subsequent compiled-source delta is independently retained claim overflow ordering. Full security acceptance, excluded domains and transitive external-program review remain open.

Pass17 reconciles its narrow source deltas with the immutable [pass16 source reviews](../repro/security-reviews/pass-16/README.md). The new [applicability verifier](../repro/layered-passes/pass-17/verify_review_applicability.py) checks exact delta scope; it does not turn those historical source reviews into a complete security verdict for the new candidates.

Pass18 retains the historical four-program source security reviews and verifies exact subsequent source deltas. Its [Mayhem sizing review](../repro/layered-passes/pass-18/mayhem-sizing-review/REPORT.md) finds the retained-bps panic already correct and leaves the strict-guard structural difference bounded by proved caller assumptions. No new source patch or runtime probe is justified by that selected review.

Pass19 reconciles its explicitly enumerated source deltas with the immutable four-program source reviews. The new admin-CTO mode/6080 combinations and Fees late option failures are static-supported but not executed by the unchanged corpus. Mayhem representation and ATA-history reviews remain unresolved; no broader security verdict is claimed.

Pass20 adds only the enumerated owned-error, typed-CPI/IDL and logical-module source deltas to the immutable review chain. The first CPI generated metadata matches the original, but recursive downstream and remaining manual calls are unresolved. Upstream stopped implementations and runtime claims are preserved as inactive evidence and are not security-reviewed or adopted as current acceptance. Whole-program security sign-off remains incomplete.

Pass21 chains exact second-CPI and owned6083 substitutions to the frozen source reviews. Shared helper-default drift is explicitly recorded and limited by a full executable-AST proof for explicit compiler versions; failed outer integrity exits remain unchanged. Security sign-off, omitted-version behavior, historical compiler selection and original whole-ELF identity remain unresolved.
