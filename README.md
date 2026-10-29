# pumpfun-source

Source code for pump.fun

**Verified checkpoint progress**

| Program | Matched windows | Matched % | Raw-equal bodies | Normalized only | Unmatched | Whole meaningful ELF equal |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| [Pump Main](programs/pump/README.md) |1,019/1,035|98.5%|188|831|16|No|
| [PumpSwap / AMM](programs/pump-amm/README.md) |784/785|99.9%|784|0|1|No|
| [Fees](programs/pump-fees/README.md) |585/585|100.0%|585|0|0|**Yes**|
| [Mayhem](programs/mayhem/README.md) |441/441|100.0%|441|0|0|**Yes**|
| [Donation Relay](repro/donation-relay/canonical-exact-selection/README.md) |492/492|100.0%|492|0|0|**Yes**|
| **Total** |**3,321/3,338**|**99.5%**|**2,490**|**831**|**17**|**3/5**|

Matched windows cover **5,022,984/5,213,128 code bytes (96.4%)**.
Raw equality compares complete instruction bytes. Normalized windows mask
specified call/address operands and do not prove whole-program identity.
These counts describe the selected maintained recipes; they are not a
percentage of engineering work completed.

The [reconstruction toolchain](reconstruction/README.md) rebuilds `programs/pump` and
scores it against the captured original in `evidence/original/`.

<!-- app-progress:start -->
## Application source and feature progress

As of **2026-10-28**. The [app workspace](app/README.md) contains the SDK, frontend and independent API-compatible backend. [PRD](app/PRD.md) · [Detailed ledger](app/contracts/feature-progress.json) · [Validation](app/evidence/validation.json).

Source acquisition/extraction is separate from editable feature reconstruction and working behavior. Percentages below use explicit counts or accepted milestones; they are not estimates of engineering effort. The original backend source is unavailable.

| Source / evidence measure | Complete / inventoried | Progress | Meaning |
| --- | ---: | ---: | --- |
| Published SDK source | 31 / 31 files | 100% | Exact npm 4.3.1 source bytes; full behavior parity still unqualified |
| Frontend JavaScript capture | 648 / 648 scripts | 100% | Known scripts in the captured route/asset graph only |
| Frontend factory extraction | 5947 / 5947 inventoried variants | 100% | Extracted factories, not original source files; authenticated/unseen modules unknown |
| Public developer API contract | 67 / 67 documented operations | 100% | Specification captured; native compatibility 0 / 67 (0%) |
| Original backend source | Not observable | N/A | Implement replacement behavior from API evidence |

**Feature scoring:** source = contract/dependency mapping, editable logic, and required adapters (3 milestones). Completion = source accepted, successful behavior, failure/auth states, and UI or data consistency checks (4 milestones). A milestone needs evidence to count. Stubs, 501 responses and historical fixture replay earn no feature credit. N/A needs an explicit applicability decision.

### Backend features

| Feature family | Static API leads¹ | Native source readiness | Feature completion | Reviewed state |
| --- | ---: | ---: | ---: | --- |
| Identity / authentication | 30 | 0/3 (0%) | 0/4 (0%) | Original auth, sessions and authorization unavailable. |
| Profiles / follow graph | 70 | 0/3 (0%) | 0/4 (0%) | Local GET /profiles/verified projects daily leaders to full profiles; production PnL, identity policy and authorization remain unqualified. Family milestones remain pending. |
| Feed / posts / callouts | 39 | 0/3 (0%) | 0/4 (0%) | No native content handlers or persistence. |
| Market discovery / search | 35 | 0/3 (0%) | 0/4 (0%) | One dated price fixture; no native discovery or price service. |
| Leaderboards / competitions | 27 | 0/3 (0%) | 0/4 (0%) | No native ranking, PnL or competition logic. |
| Livestream / presence | 9 | 0/3 (0%) | 0/4 (0%) | LiveKit configuration observed; no native orchestration. |
| Coin creation / media | 4 | 0/3 (0%) | 0/4 (0%) | No upload or metadata lifecycle; SDK source is tracked separately. |
| Rewards / fees / referrals | 12 | 0/3 (0%) | 0/4 (0%) | No native reward accounting or claims. |
| Portfolio / indexing | 17 | 0/3 (0%) | 0/4 (0%) | Opt-in materialized spot positions and user trade/transfer-history reads exist; contract/feature completion stays pending. No local chain indexer, financial derivation, production compatibility or reorg handling. |
| Settings / notifications | 29 | 0/3 (0%) | 0/4 (0%) | No native preferences, notification or messaging handlers. |

¹ 330 distinct static operation candidates overall. Family leads overlap, lack confirmed origin bindings and may include privileged/excluded paths; do not sum them or treat them as a full API denominator. The 67 public developer operations currently have **0% native compatibility qualification**: `content.read` 0/18, `graph.read` 0/17, `leaderboards.read` 0/11, `moderation.read` 0/1, `positions.read` 0/7, `profiles.read` 0/13.

### Frontend features

| Feature family | Reconstructed source readiness | Feature completion | Reviewed state |
| --- | ---: | ---: | --- |
| Shared layout / navigation | 3/3 (100%) | 3/4 (75%) | Evidence-mapped responsive shell, navigation, search URL state and failure boundaries pass browser tests. The shared search dialog also reads five hash-bound synthetic profiles through the maintained user-search adapter. Live search, full original runtime and visual parity remain unqualified; milestone statuses are unchanged. |
| Home / feed | 3/3 (100%) | 3/4 (75%) | Evidence-mapped, hash-bound synthetic examples, strict local validation and honest For You/Following boundaries pass unit and browser tests. Native feed compatibility, authenticated personalization and original visual parity remain unqualified. |
| Explore / search | 3/3 (100%) | 3/4 (75%) | Authenticated one-record historical snapshot, fail-closed adapter and offline name/symbol/mint search pass unit and browser tests. Native market discovery, production ranking and original visual parity remain unqualified. |
| Leaderboards / competitions | 3/3 (100%) | 2/4 (50%) | Contract-driven read-only interface and failure paths verified. Live API success and original visual parity remain unqualified. |
| Live discovery / playback | 3/3 (100%) | 3/4 (75%) | Authenticated five-record historical discovery snapshot, fail-closed evidence adapter and local search/selection states pass unit and browser tests. Current livestream state, native API compatibility, playback, presence and original visual parity remain unqualified. |
| GO | 3/3 (100%) | 3/4 (75%) | Authenticated 25-record historical bounty snapshot, fail-closed evidence adapter, local search/filter/sort/cursor state and unavailable account actions pass unit and browser tests. Current API compatibility, authenticated flows, mutations and original visual parity remain unqualified. |
| Mayhem | 3/3 (100%) | 2/4 (50%) | Evidence-mapped state filters, sorting, strict validation and fail-closed offline states pass unit and browser tests. No archived Mayhem response, qualified live API compatibility or original visual parity is claimed. |
| Holder rewards | 3/3 (100%) | 3/4 (75%) | Published-SDK PDA derivation now offers an explicit read of public SOL/token holdings through the existing mainnet RPC service. Holdings do not establish account existence, eligibility, accrued or claimable rewards. Claims and original visual/API parity remain unavailable or unqualified. See packages/frontend/HOLDER-PUBLIC-BALANCES.md. |
| Create coin / upload | 3/3 (100%) | 3/4 (75%) | Evidence-mapped offline metadata drafting, validation, local image preview and failure states pass browser tests. Upload, wallet signing, transaction creation, token launch and original visual parity remain unqualified. |
| Profiles / social graph | 3/3 (100%) | 3/4 (75%) | Evidence-mapped, hash-bound synthetic profiles resolve by exact user id or wallet and render filtered authored posts and separate local follow-graph lists with profile navigation. Native profile/graph compatibility, authenticated behavior and original visual parity remain unqualified; no milestone status changes for this addition. |
| Authentication / wallets | 0/3 (0%) | 0/4 (0%) | Sign-in remains unavailable. An opt-in Wallet Standard public-address connection/forget workflow is implemented with source witnesses and local protocol/UI tests; it supplies no authentication, signing or persisted identity. See packages/frontend/PUBLIC-WALLET-EVIDENCE.md. Full original auth/wallet parity remains pending. |
| Portfolio / positions | 3/3 (100%) | 3/4 (75%) | Live mainnet SOL, SPL Token and Token-2022 account reads pass unit, browser and actual-RPC checks. Pump positions/PnL compatibility and original visual parity remain unqualified. |
| Settings / notifications | 0/3 (0%) | 0/4 (0%) | No local settings or notification UI. |
| Legal / fee information | 3/3 (100%) | 3/4 (75%) | Authenticated archived fee, privacy and terms documents now render through a fail-closed offline adapter with responsive navigation and corruption tests. Current legal authority and original visual parity remain unqualified. |

**Excluded (N/A, outside every feature denominator):** Support/Intercom; Terminal/Padre; Native/mobile app and app promotion; Individual coin/token detail pages; /pump-token ($PUMP).
**Deferred (N/A):** Perps/Hyperliquid; Separate PumpSwap/revenue/GO microsites.

All app percentages above are generated by `python3 app/scripts/progress.py` from the checked-in evidence and feature ledger. Verify freshness with `python3 app/scripts/progress.py --check`. Source capture is bounded by the recorded snapshot; original frontend source completeness and the full internal API surface remain unknown.
<!-- app-progress:end -->

## License

Repository code and documentation are [MIT licensed](LICENSE). Third-party
sources and artifacts retain their original licenses and ownership.
