# Completion and remaining work

## Current maintained selections

Use the [repository overview](../README.md) for the selected source/build recipes,
complete scoring reports and qualified runtime evidence. The overview currently
links [completion checkpoint 110](../reconstruction/pump-main/checkpoints/completion-pass110-20261031/README.md)
and its [machine-readable summary](../reconstruction/pump-main/checkpoints/completion-pass110-20261031/summary.json).
Those receipts describe their recorded revisions; a later working tree still
needs its own source/build bindings and validation.

Meaningful ELF equality, full loader-allocation bytes, raw or normalized window
matches and finite runtime comparisons remain separate claims. Unlinked native
reference models do not increase compiled completion. Follow the overview's
selected receipt rather than treating an older checkpoint's counts as current.

The pass-26 selection and older notes below are preserved for provenance. Their
hashes, counts and uses of “current” or “latest” describe those historical
checkpoints. The removed `repro/` references are historical links, not current
selection files. Previously stopped executions listed below remain excluded;
this status clarification does not reopen them or establish security clearance.

## Historical pass-26 selection

> The `repro/` tree these links point to was removed from `main` in `fce9f28d`; every
> `../repro/...` path below is historical and resolves at `fce9f28d^`.

Current selected artifacts must agree with [status.json](../repro/status.json) and the complete pass-26 byte/function index. Whole-file identity remains **0/4 core programs**. Dependency capture images remain **2/5**; only SPL Token is a whole-file exact raw compiler output (**1/5**). Token-2022 and Metaplex allocation images are recorded separately from shorter raw compiler output. No overall reconstruction percentage follows from finite tests or normalized function matches.

| Program | Selected executable SHA256 prefix | Differing or missing captured positions |
| --- | --- | ---: |
| Pump | `71ec4d8a646eefc8` | 9,784,703 |
| PumpSwap | `09bee0dfd751dc6a` | 9,958,512 |
| Fees | `2387f8139a13918a` | 554,122 |
| Mayhem | `ca5d4f54b14e2f67` | 501,010 |
| Donation Relay | `5f6d29410047551f` | 614,726 |
| ATA | `ba8dd8a42ca7bff4` | 307 |
| Metaplex retained image | `2c26e081f3faabf0` | 1,509 |

Positional counts include common-extent differences and missing allocation bytes; they are not semantic distance or a completion score. The 3,338 original windows remain fully represented: Pump 1,035, AMM 785, Fees 585, Mayhem 441 and Relay 492. Opaque, unmatched, ambiguous, call-conflicting and stopped rows remain explicit.

The bounded handler accounting remains 140/150, with five partial and five unrecovered dispositions. Pump virtual-params is still unaccepted, AMM create_config has no authentic positive runtime replay, and the incentive/initializer exclusions remain active. Existing finite comparisons do not certify every original branch or a complete security review.

The selected AMM one-line correction removes unsupported compared Pubkeys from collect-owner error 6048. Its unchanged 17,462-case corpus passes, and the genuine managed build equals the tested image. Original source diagnostics and all 297 unmatched original AMM windows remain unresolved. Mayhem v1.54 is selected with 14 unchanged compile inputs; 177 of 441 original windows have bounded normalized matches, seven admitted handler windows remain unmatched, and 257 remain opaque, including the excluded initializer wrapper. These pattern counts do not establish semantics or historical recipe identity.

Pump's unaccepted setter proposal and Relay's proposed fixed-source Linux measurement remain work in progress and add no accepted handler or byte-identity count. Source-origin and authority restrictions remain enforced. Exact ATA and Metaplex residuals, unclosed call/data/ownership contracts and missing authentic historical build records remain open.

Stopped executions remain excluded: the new Pump sell_v2 corrective/transfer-fee probe; Pump admin-update/claim token incentives; Mayhem initializer; old V3 token-extension leaf; additional Metaplex runtime; and filtered BuyV3 partial-fill. No new signer, PDA, owner, source-origin or history bypass, fabricated source coordinate, binary patch/padding, or flag/layout sweep is part of the current checkpoint.

## Historical checkpoint notes

Everything below is retained verbatim from the prior document for provenance. References to “current,” “latest,” candidate hashes, compiler selection, or counts in this historical text describe its earlier checkpoint. The current selection and remaining work are stated above and in the latest machine-readable status/index. Historical implementation and test claims must not be transferred to later artifacts without explicit source/build/receipt bindings.

# Completion and remaining work

The instruction-implementation measure is **140 / 150 = 93.3%**, with five partial and five unrecovered handlers. The denominator uses 56 Pump, 38 PumpSwap and 31 Fees instructions from retained official IDLs, plus 25 currently identified Mayhem handlers. Implemented means bounded reconstruction with saved comparisons; it does not establish all input behavior. Two Fees dispatches are deprecated rejection paths.

The actual byte-for-byte acceptance measure is **0 / 4 core binaries (0%)**. No defensible single overall percentage combines that with handler coverage, unknown historical source, compiler/dependency attribution and the unfinished security audit. Saved cases include repeat inputs and do not measure exhaustive coverage.

| Program | Bounded implementations | Partial | Unrecovered | Whole original ELF equal |
| --- | ---: | ---: | ---: | --- |
| Pump | 48 / 56 | 5 | 3 | No |
| PumpSwap | 37 / 38 | 0 | 1 | No |
| Fees | 31 / 31 | 0 | 0 | No |
| Mayhem | 24 / 25 | 0 | 1 | No |

The current four candidates retain **53,787 differential comparison receipts**; Pump contributes 9,269 across 40 suites and separately passes 1,024 Surfpool comparisons. Complete instruction dispositions are in [completion.json](../repro/completion.json). Every implemented instruction remains subject to unmatched whole-binary, transitive data/call, diagnostic and exhaustive-input gaps.

Current Pump is the [buy-order checkpoint](../repro/pump/buy-mode-order-fortyeight/README.md) (`bc677505…`, 1,588,408 bytes). Its admitted buy path rejects complete before cashback. Exactly nine executable bytes change; all bytes outside buy and the entire exact-quote body match the preceding fee-basis build. All 9,269 differential and 1,024 Surfpool comparisons pass. Existing inspected fixtures lack the combined-flag and divergent-supply cases. Current Fees is the [V2 caller checkpoint](../repro/pump_fees/v2-caller-v144/README.md) (`b2d02994…`, 852,248 bytes): V2 payout composition and the retained Pump client are integrated; all 17,461 comparisons and the separate ten-step sequence pass again. Both full main executables and symbol ELFs equal their tested scratch outputs. Neither matches its captured original. The legacy comparison-value correction and V2 caller composition are integrated with bounded evidence; complete original identity remains open.

Current AMM is the [accumulator-order checkpoint](../repro/pump_amm/accumulator-order-v144/README.md) (`8ce5f958…`, 1,199,072 bytes). A clean main executable and symbol ELF equal the separately tested scratch candidate. The accumulator user assignment now follows successful Clock retrieval, matching the original ordering. All 17,462 existing comparisons and 35,418 signature checks pass; no new case or initializer-success fixture was added. Complete before/after function, call and data ledgers still contain 310 unmatched original windows. The complete 2,912-byte fee-update handler, wrapper and event serializer retain their normalized matches; 12/16 immediate handler targets match. Scalar methods, recipient source coordinates, transitive data and authentic successful initializer replay remain unresolved. The source-order correction does not establish a committed-state difference on a reverted transaction.

The Pump, AMM and Fees checkpoints bind clean main binaries to their separately tested scratch builds and retain independent main input/provenance bindings. The 140/150 bounded measure and 0/4 whole-original equality measure remain unchanged. The `unrecovered` accounting bucket includes static-only initializer work that has not met bounded runtime acceptance.

## Instruction work still incomplete

- **pump.admin_update_token_incentives** — unrecovered.
- **pump.buy_exact_quote_in_v3** — partial. Bounded SOL and synthetic USDC Token/Token2022 quote paths, configured creator fee/gross-spend truncation, funded completion using actual base-vault balances, optional fills and Mayhem crossing. Nested routes, transfer-fee extensions and exhaustive account validation remain unresolved.
- **pump.buy_v3** — partial. SOL and USDC quote branches, Mayhem/holder fields and cashback rejection. Other quote routes and exhaustive extension/account validation remain incomplete; final event suffix uninterpreted.
- **pump.claim_token_incentives** — unrecovered.
- **pump.create_v2** — partial. Normal SOL and admitted quote creation, holder/quote-control/configured-fee paths, plus ordinary Curve/Pool ancestry with finite depth-one through depth-five validation. The 16 added cases use synthetic pre-existing canonical ancestry. Mayhem, exhaustive ancestry/error coverage, and new Token-2022 ancestry/extension modes remain unresolved.
- **pump.multi_hop_curve_swap** — partial. Prior one/two-curve ordinary routes and sixteen successful three-hop Tokenkeg cases through genuine AMM PDA-signed invocation are retained. The added cases exercise both directions, four fee configurations and two amounts with existing canonical accounts. Arbitrary hop counts, native/WSOL variants, other quote currencies, completion/migration, short-account resizing, Token-2022/extensions and holder/cashback/Mayhem modes remain incomplete. Source domain fences are not claimed original rejection behavior.
- **pump.sell_v3** — partial. SOL and USDC quote branches, Mayhem/holder fields and cashback rejection. Other quote routes and exhaustive extension/account validation remain incomplete; final event suffix uninterpreted.
- **pump.set_mayhem_virtual_params** — unrecovered.
- **pump_amm.create_config** — static-only implementation compiled; no authentic positive initializer replay, so not counted as a bounded implementation.
- **mayhem.initialize_mayhem_state** — unrecovered.

The two Pump incentive handlers and Mayhem initializer remain stopped. The confirmed Pump `sell_v2` quote transfer-fee minimum-output/event mismatch remains unresolved; that corrective probe lane is also stopped. These tasks must not be reassigned to another worker as a workaround. Earlier unintegrated v3 token-extension work and the aborted extra Metaplex runtime probe are not resumed.

`set_mayhem_virtual_params` has static body/wrapper/parser attribution but lacks a valid genuine Mayhem PDA invocation. `pump_amm.create_config` now has compiled source and complete normalized wrapper/handler/context/event comparisons, but no successful fixed-admin historical replay. No synthetic signer bypass is an acceptable substitute. The ordinary Tokenkeg two-curve extension has 20 passing comparisons: 16 successes, two AMM zero-input rejections before Pump, and two final AMM slippage rollbacks after successful Pump execution. Its genuine caller/PDA signing covers only the two directions above. The earlier one-curve-only restriction remains historical; broader routing is still unrecovered.

## Remaining binary and dependency work

- **All four core programs:** recover unmatched original functions/windows, full call targets and referenced data, historical source/module coordinates, dependency selections, compiler/SDK phases, section layout and relocation identity. Inferred disassembly windows are not verified historical function boundaries, and normalized matches are not whole-byte equality.
- **Pump:** resolve partial trading/creation/routes, unmatched helpers and recursive data/call attribution. The [sixth layered inventory](../repro/layered-passes/pass-06/REMAINING.md) binds all current bytes and complete windows. The 1,840-byte serializer, all 25 immediate targets and discriminator remain matched; four PumpError metadata bodies and 62 immediate targets also retain their matches. The connected decoder/preparation source is integrated, but its original split bodies are not normalized-identical. Original call-consistent windows move 455→454; raw-equal pairs remain 617. Broader mode/whitelist, residual/settlement/event composition, short-layout runtime acceptance and diagnostic/transitive data remain unresolved.
- **PumpSwap:** attribute unmatched windows, transitive data and admin source-location differences; current Pool and GlobalConfig serializers match under documented normalization. No fabricated source padding or diagnostic locations.
- **Fees:** all 31 bodies have bounded coverage; parser details, transitive helpers/data, source locations, compute use and full ELF identity remain unresolved. The retained eight-package Solana-family recovery improves six helpers and the formatter. The current inline-initializer correction additionally matches the complete 2,992-byte handler, 6,824-byte parser and 1,608-byte wrapper, nine immediate handler call-target bodies and two bounded literals. These matches do not establish unlimited transitive closure or a unique historical source/dependency graph.
- **Fees donation and sharing handlers:** the [current V2 caller checkpoint](../repro/pump_fees/v2-caller-v144/README.md) integrates the reviewed legacy preprocessing/payout/ownership sequence and preserves prior quote/predicate/social corrections. Complete donation, social and legacy handler bodies still differ. Fresh full inventories retain every unmatched and conflicting alternative. [V2 payout](../repro/pump_fees/v2-payout-contract/REPORT.md) and the [nonzero-quote contract](../repro/pump_fees/nonzero-quote-payout-contract/REPORT.md) remain separate implementation obligations. Historical diagnostics, transitive call/data closure and original build identity are unresolved.
- **Mayhem:** non-initializer error-return ABI/code-generation differences, five unknown GlobalParams field roles (two additional withdrawal-interval roles are now statically attributed), compiler/stdlib provenance and diagnostic differences remain. Twenty-six panic diagnostic differences include eight unwrap-detail differences. The initializer lane remains stopped.
- **SPL Token:** exact captured 108,600-byte payload rebuilt.
- **Token-2022:** exact captured payload rebuilt, including separately regenerated zero allocation padding.
- **Associated Token Account:** authentic historical build recipe missing; 307 raw bytes differ (304 text, three relocation). All 159 inferred windows correspond under the recorded address mapping, which is not raw equality.
- **Metaplex:** 1,250 / 1,251 raw windows match. Utilize is the remaining 5,104-byte body; 1,509 total differing bytes include text/source-coordinate/relocation differences. The 86,543-byte captured allocation tail is verified zero. Existing 135 comparisons do not cover every zero-use boundary.
- **Donation relay:** [build08](../repro/donation-relay/source-build-08-whitelist-writer/README.md) implements owned serializer/interface/close errors and the whitelist I/O error/drop boundary and has no backend stack-limit failures. [Twelve unchanged ordinary local comparisons](../repro/donation-relay/build08-ordinary12/ordinary.json) pass. The complete writer retains its normalized match. Complete serializers, error conversion, name decoration and log bodies remain unequal. The current inventory retains 492 original/301 candidate windows, 33 raw original matches, 121 normalized original shapes and 371 unmatched originals. The earlier source-origin rejection was not rerun. Six fixed-authority success routes, full call/data/error ABI and historical source/build provenance remain open.

The [five-helper Pump arithmetic ledger](../repro/pump/wide-runtime-attribution/README.md) closes compiled-body and internal-call correspondence across 5,960 bytes of the accepted candidate. Three bodies match raw; the remaining six differing bytes are call displacements with verified destinations. The separate [manual numeric contracts](../repro/parallel-work/2026-10-25/composition-results/pump_route_wide/REPORT.md) address positive-denominator arithmetic. Historical runtime source/build linkage, surrounding route admission/transfer/event behavior and whole-program equality remain open.

## Build verification and audit work

Two fixed-source Linux Fees attempts stopped before compilation. The first exposed an SDK installer provenance difference; the second stopped at the fetch/empty-target guard without enough retained state to distinguish its cause. Local reproduction proves that fetch can create `.rustc_info.json`; the helper now separates fetch and compilation targets and retains both states. The corrected pipeline passes 30 preparation and retention tests.

The recorded Darwin pipeline compiles Pump/Fees with v1.44 but strips through SDK-selected v1.52. The official Linux SDK defaults to v1.43 at that stage. The corrected fixed-source Linux pipeline pins both official tool distributions and the exact retained SDK, with a process trace and phase identities. [Hosted run 40166255149](https://github.com/lalalune/pumpfun-source/actions/runs/40166255149) completed one source build at frozen revision `4ffe8bd88761059693e481ae972443c10204f7af`. Its 768,984-byte candidate `7e823e605097cdba7a3d782a2f20edaee9980d7d5a29822ac7d1a43400620133` differs from both the captured original and the earlier Darwin build; no runtime validation or receipt transfer is claimed. The [bounded hosted evidence](../repro/pump_fees/linux-v144-hosted-comparison/README.md) includes the candidate and actual compiler-entry traces. This establishes an executable controlled comparison, not the original historical recipe or binary equality. No version/flag/path brute-force search or binary patching is authorized.

The security audit remains incomplete. Existing malformed-input/lifecycle checks and reconstruction regressions do not constitute a full review of every current handler, account relationship, CPI, arithmetic boundary or deployment configuration. Current source review and evidence applicability must be reconciled before any sign-off.

## Parallel ownership

The ordinary Tokenkeg two-curve extension and Fees inline-initializer correction now have validated main-path checkpoints; broader routing and whole-binary reconstruction remain open. Native workers also maintain portable function inventories. The first additional CLI pass assigned nine workers in separate scratch directories for Pump event attribution, Pump partial-path gap mapping, AMM residual functions, Fees residual functions, Mayhem non-initializer ABI, ATA recipe evidence, Metaplex Utilize attribution, donation-relay reconstruction and audit evidence coverage. They must preserve all stopped lanes, avoid duplicate compilation and return reviewable evidence before root integration.

A worker covers related functions as a dependency-aware group. Launching one process for every inferred disassembly window would duplicate helper analysis and would not establish completion. Each machine inventory retains every row, including unmatched and unresolved rows.

See [parallel ownership and configuration](PARALLEL_WORK.md) for the launched assignments and documented concurrency setting.

The [portable function inventories and follow-up studies](../repro/function-inventory/2026-10-24-374fcf0/README.md) preserve every row from the historical baseline, plus seven static studies/build proposals. Those baseline Pump/Fees tables are historical and remain distinct from the current two-curve and inline-initializer candidates.

The [first parallel research pass](../repro/parallel-work/2026-10-24/results/README.md) now supplies refreshed Fees residuals, every AMM residual row, 74 Pump partial-path gap rows, all 492 relay window dispositions/codecs and detailed ATA/Metaplex provenance. Eight public packages pass portable verifiers. These new analyses add no accepted handlers or whole-byte matches; subsequent scratch proposals are tracked separately.

The [second parallel research pass](../repro/parallel-work/2026-10-24/wave2-results/README.md) adds seven verified static/source packages. It includes the static source evidence for the Fees inline-account correction subsequently built and validated in the current checkpoint, uncompiled module reorganization, four relay wire parsers and arithmetic fragments, two newly attributed Mayhem fields and a public-source-only audit backlog. The correction adds no handler or unique comparison case. Scratch proposals and original-only fixtures do not change accepted completion counts.


The [third parallel pass](../repro/parallel-work/2026-10-25/results/README.md) includes frozen candidate-source reviews for all four programs and six static continuations. The reviews enumerate 112 included account contexts and 422 function declarations/dispositions with 25 unresolved candidate observations. This is review progress, not security sign-off or confirmed captured-original vulnerabilities. Their fixed source checkpoint is 517d77d; subsequent source changes require explicit applicability review. The [Linux/Darwin attribution](../repro/pump_fees/linux-darwin-v144-attribution/README.md) finds no additional original function-body matches, but 14 source-location tuple improvements favor the retained Linux-distributed sysroot path family without proving a unique build host.


The [five context-closure results](../repro/parallel-work/2026-10-25/context-closure-results/README.md) and their [independent review](../repro/ci/context-closure-review/README.md) support broader ordinary route/native/nested-create contracts. Two [concrete Pump source hypotheses](../repro/parallel-work/2026-10-25/source-hypothesis-results/README.md) express general ordinary Tokenkeg routing and deeper Curve/Pool creation. Their original publication packages record uncompiled proposals; the subsequent [nested-ancestry checkpoint](../repro/pump/nested-ancestry-fortyeight/README.md) now has bounded main-source acceptance. The [historical Fees 8f89 inventory](../repro/pump_fees/function-inventory-8f89/REPORT.md) retains every one of 585 original and 548 candidate windows, including ambiguity and 110 candidate/148 original residual rows. Static pattern correspondence is not a substitute completion percentage.

The [integrated source proposals](../repro/parallel-work/2026-10-25/integration-hypothesis-results/README.md) identified concrete relay and BuyV3 application boundaries for the [eight closure assignments](../repro/parallel-work/2026-10-25/application-closure-followups/README.md). Their successor source packets are described below. General ordinary routing has a corrected buyback preflight and passed [independent source review](../repro/pump/general-route-corrected-review/REPORT.md); actual build/runtime acceptance and main integration remain separate gates. Native workers handle nested creation, route compilation/validation and relay dispatch composition. These assignments do not change the 140/150 or0/4measures.


The [application-closure source packets](../repro/parallel-work/2026-10-25/application-closure-results/README.md) now supply explicit proposals for relay context parsing, six mint-policy scans and nine generated exits, plus BuyV3 volume admission/initialization, native settlement and event fields. They narrow the missing application logic but remain uncompiled and unintegrated. The [BuyV3 fee proposal](../repro/parallel-work/2026-10-25/buy-fee-closure-result/README.md) supplies the actual mint-supply threshold, quote-key table choice and per-leg fees; context/error integration remains necessary. The [relay dispatch proposal](../repro/donation-relay/dispatch-source-proposal/README.md) supplies eleven wrapper paths while preserving explicit IDL/runtime boundaries. Two CLI workers now compose these source fragments. The [nested depth correction](../repro/pump/nested-depth-guard-review/REPORT.md) retains the historical failed diagnostic comparison; its corrected source has since passed the [nested-ancestry checkpoint](../repro/pump/nested-ancestry-fortyeight/README.md). None changes the ten incomplete handler dispositions or whole-binary equality.

The [current-source reviews](../repro/parallel-work/2026-10-25/current-audit-results/README.md) reconcile Fees and AMM at published checkpoint `7a9cf01`, including their changed contexts and functions. They narrow observation applicability while preserving unresolved policy, runtime, deployment and original-code premises. The security audit remains incomplete.

The [first layered pass](../repro/layered-passes/pass-01/README.md) records seven complete static inventories and separate exact SPL dependency checks. All rows, ambiguous pairings, uncovered data, headers, relocation records and excess tails remain visible. Its independent [BuyV3 review](../repro/pump/buy-v3-composition-review/REPORT.md) identifies 105 accepted successes that the uncompiled replacement would exclude; integration is held until those paths are preserved before account parsing. The Mayhem field crosswalk also needs an exact-token correction. Neither finding changes accepted handler counts.

The [corrected Mayhem field crosswalk](../repro/layered-passes/pass-01/followup-results/mayhem-field-crosswalk/REPORT.md) removes twelve false substring references to `MayhemState.field_8`; they actually use `field_89`. Historical ledgers remain immutable. The five unknown GlobalParams roles and neutral MayhemState fields remain unresolved.

The [fourth layered pass](../repro/layered-passes/pass-04/README.md) rechecks every byte range, adds current frozen-source audit ledgers for all four programs, and advances BuyV3 preparation, fees, vault, settlement and event contracts plus the Fees legacy caller proposal. Those proposals remain unaccepted. The dependency reconciliation rejects unsupported ATA toolchain/function claims and byte-closure predictions; whole-file equality and security sign-off remain incomplete.

The [sixth layered pass](../repro/layered-passes/pass-06/README.md) publishes Pump decoder/preparation integration, Relay owned-error source/build/runtime evidence, the BuyV3 whitelist/mode contract, and uncompiled Fees V2 and legacy-value proposals. Its complete before/after byte ranges and current function-ledger index retain every mismatch. Agent usage-limit interruptions are recorded as unfinished work. Whole-file acceptance remains 0/4 core and 2/5 dependency captures.

The [seventh layered pass](../repro/layered-passes/pass-07/README.md) integrates the one-check Fees diagnostic correction after a fresh build, all existing comparisons, saved-signature verification and a byte-identical clean main rebuild. Its full inventories retain the same original-window dispositions. No new cases, handler counts or whole-original identity are claimed.

The [eighth layered pass](../repro/layered-passes/pass-08/README.md) adds five normalized Fees function matches and restores Relay whitelist I/O error construction/drop ordering. These improvements add no whole-original identity matches or new test cases. AMM Clock-order and Pump whitelist/settlement proposals remain separate until their own acceptance checks finish.

The [ninth layered pass](../repro/layered-passes/pass-09/README.md) integrates AMM accumulator ordering and repeats the complete byte comparison. Its fresh dependency review reconfirms 307 ATA and 1,509 Metaplex differing positions without a justified additional source patch. No whole-original identity count or bounded-handler count changes. The separately reviewed Pump buy fee-basis and Mayhem typed-error changes are not accepted by this checkpoint.

Current Mayhem is the [swap-sell typed-error checkpoint](../repro/mayhem/sell-result-error-twentyfour/README.md) (`7d416f84…`, 668,640 bytes). Both swap buy and sell now construct the reviewed typed zero-divisor error. All 9,595 functional comparisons pass with 61 diagnostic rows, including three second-burn source-location differences. Saved verification checks 13,284 retained transaction strings and 26,500 signatures. The 19,190 recorded/derived signed executions are not a universal raw-signature claim. Main and scratch executables and symbols match.

The [tenth layered pass](../repro/layered-passes/pass-10/README.md) publishes both source corrections, independent reviews, clean-main build identities and full updated byte/function/call/data ledgers. Six more Fees residuals were reviewed: three suspected ordering differences already match, while three ownership/function-boundary gaps lack a justified correction. No handler-completion or whole-original identity count changes.

The [eleventh layered pass](../repro/layered-passes/pass-11/README.md) publishes the buy-order and swap-sell corrections with full updated byte/function/call/data evidence. It also records a supported AMM formatter-source proposal, whose separate build is not counted as an accepted artifact here. Exact acceptance remains 0/4 core and 2/5 dependency captures; bounded instruction coverage remains 140/150.

The [twelfth pass](../repro/layered-passes/pass-12/README.md) integrates the AMM formatter restoration (`d3dacf1b…`, 1,196,544 bytes). Its 1,520-byte renderer, buffer/UTF-8 error formatters and immediate call targets match under existing normalization. Four additional original windows match, leaving 306 unmatched; recursive data and truthful source-location differences remain. All 17,462 unchanged comparisons and 35,418 saved signatures pass; main and scratch complete artifacts match. Whole-original acceptance remains 0/4 core and 2/5 dependency captures, and bounded instruction coverage remains 140/150.

[Pass14](../repro/layered-passes/pass-14/README.md) advances the Relay checkpoint to IDL owned-header errors (`977fa996…`,469,016 bytes). All12 unchanged ordinary cases pass. Two further original windows gain normalized matches, leaving369 unmatched. Dependency capture exactness remains2/5 and core exactness0/4.

[Pass15](../repro/layered-passes/pass-15/README.md) integrates the Fees withdrawal owned-error and AMM claim-context corrections. Fees retains17461 passing comparisons and ten sequence steps; its final missing-token-program error remains static-only. AMM retains17462 passing comparisons and35418 verified signatures, with four additional normalized original windows and302 unmatched. No whole-original or security completion count changes.

[Pass16](../repro/layered-passes/pass-16/README.md) preserves the counts:140/150 bounded paths,0/4 exact core programs and2/5 exact dependency captures. Pump creator paths now use full recovered curve decoding; AMM rejects claim accumulation overflow before clearing rewards. All9269 Pump comparisons plus1024 Surfpool comparisons and17462 AMM comparisons pass. These finite counts do not measure exact reconstruction completion.

[Pass17](../repro/layered-passes/pass-17/README.md) preserves the140/150 bounded count and0/4 whole-core result. AMM still has302 unmatched original windows; Fees retains130 unattributed and2conflicting original windows; Relay10 retains370 unmatched original windows. The source corrections and runtime preservation do not establish full body, data or indirect-call equality.

[Pass18](../repro/layered-passes/pass-18/README.md) retains140/150 bounded paths and0/4 exact core programs. AMM's Sync parser/wrapper add two normalized original matches, leaving300 unmatched; all113 existing no-change logs match. Fees' corrected predicate has full static truth-table support but no changed-domain input among116 existing sharing cases. Relay11 retains370 unmatched original windows.

[Pass19](../repro/layered-passes/pass-19/README.md) retains140/150 bounded paths and0/4 exact core programs. Admin-CTO special cashback/6080 paths and Fees late missing-option paths remain without runtime coverage. AMM initializer parser/wrapper/handler add three normalized original matches, leaving297 unmatched. Neither those matches nor the53,787 finite core comparisons establish exhaustive semantics.

[Pass20](../repro/layered-passes/pass-20/README.md) preserves140/150 bounded implementations and0/4 core byte identity. Fees adds three complete normalized helper matches, leaving127 unattributed and two conflicting original windows. AMM remains297 unmatched. Pump6088 named-error behavior is confirmed by existing cases. All upstream-only implementation claims remain inactive pending permitted verification.

[Pass21](../repro/layered-passes/pass-21/README.md) retains140/150 bounded implemented paths and0/4 core identity. Fees closes two more complete normalized helpers, leaving125 unattributed and two conflicting original windows. Pump6083has six differential but zero signed cases. Both scratch outer integrity failures remain recorded; only the exact helper-default transition is reconciled, not ignored.

The [twenty-second layered pass](../repro/layered-passes/pass-22/README.md) retains140/150 bounded paths and0/4 core byte identity. All four sharing CPIs use typed APIs;122 unattributed and two conflicting original Fees windows remain. Five CTO owned guards and Relay3002 are corrected. Full cursor/branch proof identifies a remaining Fees admin-or-creator authorization difference; it is not yet integrated. Exact remaining bytes and scope limits are published with the pass.

[Pass23](../repro/layered-passes/pass-23/README.md) integrates the proved Fees sharing authorization correction and current source-review CI wiring. All17461 existing comparisons and10steps pass, with zero admin-only runtime cases. Whole-original identity remains0/4; ATA source/build order and all listed recursive/data/source/security gaps remain.

[Pass24](../repro/layered-passes/pass-24/README.md) integrates the proved Pump6030/application2006 compared-key tuples and Relay13 checked-borrow ownership. All 9,269 existing Pump differential cases, 1,024 signed comparisons, and 12 ordinary Relay cases pass; the changed application2006 and Relay borrow-failure branches have zero runtime coverage. The four remaining numeric CTO sites, all partial/unrecovered handlers, opaque exclusions and full call/data/source/security obligations remain open. The compiler-only Mayhem v1.54 candidate is not selected by this checkpoint.
