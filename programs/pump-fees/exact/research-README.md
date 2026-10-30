# Partial Pump Fees reconstruction

All 31 IDL instruction bodies now execute bounded recovered behavior: `get_fees`, `get_fees_with_quote_mint`,
`set_authority`, `set_social_claim_authority`, `set_disable_flags` and
`set_claim_rate_limit`, `initialize_fee_program_global`, `update_fee_config`,
`update_stable_fee_config`, `set_exotic_flat_fees`, `extend_fee_config`,
`revoke_fee_sharing_authority`, `transfer_fee_sharing_authority`, `upsert_fee_tiers`,
`upsert_stable_fee_tiers`, `update_admin`, `create_donation_fee_pda` and
`crank_donation_fee_pda`, `create_social_fee_pda`, `claim_social_fee_pda` and
`claim_social_fee_pda_v2`, `withdraw`, `initialize_buyback`, `update_buyback_authority`,
`update_buyback_claim_rate_limit`, `sweep_buyback`, `create_fee_sharing_config`,
`admin_cto_sharing_config`, `update_fee_shares`, `update_fee_shares_v2` and
`initialize_fee_config`. Two of these are deprecated rejecting dispatches.
All instruction bodies being present does not establish every account constraint,
historical source identity, complete security coverage or byte equality. Some
sharing-reset constraints are tested only through the genuine Pump caller. This
crate remains an experimental reconstruction target, not a deployable substitute.

The interface scaffold originated in `research/imported-lab/reconstruction/pump-fun-fees-candidate`
(source commit and unchanged upstream hashes in `research/import-manifest.json`).
This working copy adds actual query implementations, PDA constraints using the
stored bump, optional trailing bool parsing, and the custom FeeConfig parser.
Original program bytes are comparison inputs only and never compiler inputs.

Four buyback handlers add 1,249 cases, including all u8 indexes, ordinary authority
signatures, initialization, native/token sweeps, rate limits and checked counters.
Vault initialization accepts indexes 0–7 and leaves the authority zero until a
global-authority update. Sweeps transfer tokens before native SOL and retain rent
for the actual allocation. A zero rate bypasses cooldown; other rates use a strict
signed elapsed-time comparison. The observations and limits are detailed in the
buyback draft (formerly `localnet/recovery/fees-buyback/README.md`, removed from the tree).

Sharing creation adds 116 cases with genuine captured Pump and PumpSwap CPIs.
The handler creates a version-two sharing account, validates creator authority,
and transfers the curve/pool creator role through the captured programs. Graduated
coins require AMM accounts. Existing nonzero sharing versions return early.
Temporary serialized creator/admin state before each CPI is retained, because
the called program reads that state. These cases use normally signed test-owned
keys and synthetic local accounts; they do not prove every live sharing transition.

The current source checkpoint (formerly `repro/pump_fees/sharing-owned-error-v144/README.md`, removed from the tree)
binds this README and all 25 remaining source/workspace/IDL inputs. It preserves
the recovered dependency graph, social-account layout, inline initializer Pump
Global account, four declarations in `state.rs`, and SharingConfig in
`instructions/fee_sharing/create_fee_sharing_config.rs`. The tested scratch ELF is
849,984 bytes, SHA-256
`70ddf61ad431b950aefd736ac50da156c9079257ea95f32cfcd9635266e40429`. Main-build identity must be recorded separately before these
receipts are attributed to a main build.
Its 17,461 comparison receipts comprise the unchanged 17,441-receipt corpus
(including 69 repeated-input checks) and the unchanged 20 focused comparisons.
All inputs are repeats in this checkpoint; no new handler or unique case is added.
The ten-step persistent donation sequence is separate. Two authentic historical
FeeConfig initializer messages retain their signed bytes and signature verification;
these are not historical FeeProgramGlobal initializer messages. Saved ordinary
transaction fields re-verify 17,204 signatures across 8,644 encoded baseline and
sequence fields; those are not unique transactions or extra cases. Focused20 adds
40 signed executions and 80 test-owned signatures, counted separately. Some older
reports preserve runtime signature assertions without complete transaction bytes.
All eleven fresh scratch jobs have retained numeric zero exits, complete reports
and logs. Main-source acceptance carries those receipts only by whole executable
and symbol identity; target transactions are not repeated for the main build.
Compilation selected platform-tools v1.44; the unchanged SDK installer selected
v1.52 for `llvm-objcopy` stripping. The phase records distinguish those tools;
retained file hashes do not retrospectively prove every historical invocation.
Full-file equality with the captured original remains false, and the unique
historical dependency/compiler recipe remains unresolved. The
prior donation business checkpoint (formerly `repro/pump_fees/donation-business-v144/README.md`, removed from the tree)
retains its 770,744-byte `fc1088f3…` executable and original focused20 coverage.
The donation event-account checkpoint (formerly `repro/pump_fees/donation-event-account-v144/README.md`, removed from the tree)
retains its 768,848-byte `8f89dbeb…` executable and limitations; older
SharingConfig (formerly `repro/pump_fees/sharing-module-v144/README.md`, removed from the tree),
state-module (formerly `repro/pump_fees/state-module-v144/README.md`, removed from the tree) and
inline-context (formerly `repro/pump_fees/initializer-inline-v144/README.md`, removed from the tree)
checkpoints also remain immutable.

`CreateDonationFeePda` retains its owned `AccountInfo` event authority, seed/bump
constraint and typed program field. Its complete normalized 8,984-byte parser and
928-byte wrapper still match with identical relocation patterns. Of their 76
paired direct calls, 74 target windows match; the handler and parser initialization
closure remain distinct. The closure retains natural source-location differences.
These results do not establish arbitrary descendant/data closure.

The donation handler now restores the original reserve-dependent BondingCurve
branch and two early logs. A nonzero reserve selects the typed curve creator and
raw quote extension at bytes 83–114 when allocation is at least 115 bytes; a short
or zero curve quote defaults to wrapped SOL. All-zero reserves retain the typed
Pool path. Shared-admin authorization omits compared keys; direct creator and
Pool-address errors preserve the original Left/Right order. PDA derivation errors
use the directly evidenced origin-free InvalidPool conversion. Typed accounts,
borrow boundaries, guard order, state writes and event CPI remain preserved.

All20 focused cases compare complete watched state, events, inner instructions,
return data, errors and semantic logs with ordinary signatures, blockhash checks
and default transaction history. At the prior business checkpoint, eight repeated
existing inputs and twelve added typed curve/sharing combinations; all20 are
repeated unchanged here. Eleven saved baseline rows additionally check early
logs, guard order and compared-key diagnostics without executing more transactions.
Raw logs remain unequal: compute-unit lines and truthful source-coordinate spans
are excluded from semantic log equality, while error-origin presence and compared
keys stay strict. The loaded program account's ELF fields and initial rent are
normalized because the binaries differ. The two reviewed Pool and sharing-account
`AccountInfo` temporaries are now borrowed without cloning. The new handler is
12,864 bytes versus the original inferred 13,800-byte window and remains unmatched
after normalization; its size change does not establish improved byte distance.
The complete data check preserves 19 directly referenced objects and six business
error messages. One formerly direct `AccountInfo::clone` call is absent; inlined
reference-count operations are not counted by that observation. Passing fixtures
do not prove complete behavior, indirect/transitive closure or source identity.

The fresh inventory preserves all 585 original inferred windows and 575 candidate
symbol windows. Original status is 453 mapped patterns, 130 unattributed and
two call conflicts. The candidate has 455 consistent normalized call patterns,
118 unmatched windows and two call conflicts; 101 windows are raw-identical.
Against the prior 8ff12 legacy-quote/social-admission checkpoint, eight previously
unattributed original windows and one conflicting window gain mappings. All
original rows, ambiguities and immediate-call residuals remain recorded; these
mechanical window categories are not a historical-function denominator or
semantic completion percentage. Whole-file equality remains false.

The two sharing AMM predicates now preserve the original conjunction, and the
donation quote helper borrows its AccountInfo argument. Legacy `update_fee_shares`
first checks the curve quote bytes at 83..115 when the allocation is at least 115
bytes; short allocations are admitted by this helper. A nonzero quote returns
UnsupportedQuoteMint before the already-updated version error. The fresh machine
code confirms the borrow release and temporary drops before this error branch.
The helper is inlined; the complete legacy handler still differs from the original.
The legacy caller now applies the recovered remaining-account preprocessing,
including its conditional final-account admission and slice shortening, before
the AMM adapter. It owns the fixed AMM accounts before reserve/owner checks and
uses the generated CPI clients. Legacy authorization preserves its compared-data
and direct revoked-admin conversion. Payout preparation validates each available
account before executable-account filtering, retains the original rescaling and
first-maximum remainder behavior, and serializes a changed sharing list before
calling Pump. Empty payout accounts skip that CPI. Final list validation retains
checked totals, sorted duplicate detection, and the observed error ordering.
The existing 417 sharing-update rows pass again. That legacy recovery preserved
V2 source; the current V2 caller recovery below changes its body while retaining
both account contexts. No new cases are added.

The generated Pump distribution CPI, both programs' four meta/info helpers,
SharingConfig exit and event match their complete original normalized windows
and 96 immediate target bodies. The AMM generated CPI remains nonidentical and
has an actual outlined owned-account cleanup call. The original helper partition
is not reproduced: the current legacy handler is 15,384 bytes and some source helpers
are outlined. Full legacy/V2 CFG and data closure and diagnostic coordinates
remain unresolved. Five accepted social roots and their 176 immediate targets
retain their prior normalized matches. Existing account declarations remain
unchanged while the V2 handler body is reconstructed. No original whole-program equivalence is
claimed. The prior legacy-quote/social-admission package (formerly `repro/pump_fees/legacy-social-admission-v144/README.md`, removed from the tree)
retains the 773,808-byte 8ff12 ELF, source and tested receipts unchanged.

Social token claims use a shared admission helper for both associated accounts.
It checks the canonical address, System-owned creation permission, exact supplied
token-program owner and decoded mint. Recipient creation uses the ordinary
idempotent associated-token instruction with six AccountInfos; the source-side
call disallows creation. Fresh bytes confirm both flags and instruction opcode 1.
All 17 original immediate helper target windows have normalized matches called by
the new helper, and the six-AccountInfo drop body is raw-identical. Complete
helper/handler equality and unrestricted descendant/data closure remain unresolved.
No new fixtures or token-extension conclusions are added by this checkpoint.

The prior donation-borrow checkpoint (formerly `repro/pump_fees/donation-borrow-v144/README.md`, removed from the tree)
retains its 770,016-byte `5cf8d567…` ELF and source-specific results unchanged.

`BuybackVault`, `SocialFeePda`, `DonationFeePda`, `FeeProgramGlobal` and
`SharingConfig` preserve their complete account declarations byte-for-byte, with
public reexports at their former locations. Their five complete checked codecs
now reference the original filenames and account-name literals. After
call/relocation normalization, only the historical line immediate differs:
the four state.rs attributes use natural lines 3, 6, 9 and 12 versus original
50, 113, 135 and 154; SharingConfig uses natural line 5 versus original 37.
No source padding or line alignment is used. The 35 immediate codec calls resolve
to 11 complete normalized target bodies. The prior SharingConfig checkpoint separately retains
the full 1,472-byte unchecked decoder, 1,024-byte Account::try_from wrapper and
23 immediate call sites, overlapping that checkpoint's wider codec check. The larger donation
handler remains unmatched and unrestricted descendants/data remain unresolved. ConfigStatus,
Shareholder, handlers and account contexts stay unchanged by this placement move.

The prior v1.44 checkpoint (formerly `repro/pump_fees/all-thirtyone-v144/README.md`, removed from the tree)
passes 112 independent Surfpool comparisons with 224 signed local transactions.
All Surfpool counts below refer to that retained executable. The historical
authority-guard build passes 17,384 SBF comparisons and the donation sequence;
twelve of those comparisons repeat existing indices/keys with stronger raw-log
assertions. The enum restores four omitted IDL variants and the original literal
`format` messages for errors 6003 and 6011.

The sharing reset and two update handlers add 480 comparisons. Reset runs through
the captured Pump administrative caller and its own PDA-signed CPI. Sharing
updates distribute old fees through the captured Pump/AMM programs, then validate
the new list and revoke further administrator updates. Failure rolls back the
earlier transfers. The source preserves the observed one-to-ten, nonzero,
unique-shareholder and checked-u16 total constraints and error ordering.

The final initializer adds two exact historical signed-message replays and 28
ordinary-signer rejection cases. The original administrator's public signature
is verified; the signed message is unchanged. Only stale-blockhash freshness is
adapted for local replay. The 2,512-byte account, zero defaults, rent/balances and
events match both the captured executable and saved historical transaction
metadata. These are two initialization paths against a later executable, not a
complete historical bank reconstruction. See the evidence (formerly `repro/pump_fees/initializer-history/REPORT.md`, removed from the tree).

Observed parser rules: wrong discriminator or allocation below 2,512 bytes returns
InvalidAccountData; malformed vector serialization returns BorshIoError. Standard
Anchor ownership and initialization checks run before deserialization, followed by
the config-program PDA constraint. These are tested recovered rules, not a claim
that every account migration/version path has been recovered.

Anchor 0.30.1 gave the wrong short-discriminator error (100 rather than original
101); 0.31.1 matches that behavior. The repository-root Cargo.lock pins the selected dependency graph,
which is not established as the historical graph. The full candidate still differs
substantially from the original binary. The experimental standalone fragments in
`recovered/` are separate compiler experiments; the crate builds `src/`.

```sh
python scripts/prepare_locked_cargo_home.py --lockfile Cargo.lock \
  --output work/fees-cargo-home
CARGO_HOME="$PWD/work/fees-cargo-home" python scripts/build_partial_candidate.py --manifest programs/pump-fees/Cargo.toml \
  --program pump_fees --artifact-name pump_fees_candidate.so \
  --tools-version v1.44 --output work/fees-clean-build \
  --extra-input programs/pump-fees/README.md
python scripts/fees_validate_all.py \
  --candidate work/fees-clean-build/artifacts/pump_fees_candidate.so \
  --output work/fees-handler-validation.json
```

Use a Python environment with root requirements installed and cargo-build-sbf
2.1.21 with platform-tools v1.44 for compilation and the retained SDK's v1.52
stripping tools available. The cache helper requires previously
downloaded crates and verifies archives against Cargo.lock. Build offline from the pinned lockfile;
source/toolchain/build-log hashes and the raw full-file comparison are retained.
The runtime comparison checks return bytes, error codes, and unchanged account
state/lamports for queries. It does not assert log strings, compute usage, or byte
identity. Synthetic invalid account states are included and do not establish
reachability or a vulnerability.

The four administration handlers use a 338-byte FeeProgramGlobal with stored-bump
PDA verification, signing/writable authority, and custom authorization error6016.
Changing the main authority to zero fails6001; the social-claim authority accepts
zero. All u8 flag values and the tested u64 rate-limit boundaries are accepted.
Every successful setter emits the typed log event and signed self-CPI event.
444 original/candidate cases compare errors, complete state, lamports, event bytes
and inner instructions. The two query suites contribute10,838 additional cases.

The global initializer reads the older 740-byte Pump Global layout, authenticates
its authority and PDA, creates the 338-byte Fees global with canonical bump, and
emits the exact event log and self-CPI. Its 180 comparisons include prefunding,
malformed accounts, authorization, argument boundaries and CPI rollback. The
historical authority-guard checkpoint passes 17,384 comparisons; the current
31-instruction candidate passes the 17,461 receipts described above.

`InitializeFeeProgramGlobal` holds its Pump Global account inline. The original
parser's return stores establish a 1,200-byte accounts aggregate, including the
744-byte account wrapper at offsets 456–1199. Removing only this field's `Box`
reproduces the complete normalized 2,992-byte handler, 6,824-byte parser and
1,608-byte wrapper, with matching relocation patterns, nine handler call-target
bodies and two bounded literal spans. The selected Anchor language crate is
0.31.1 and the relevant locked macro crates are 0.31.2. These matches do not prove
unlimited transitive call/data equivalence or unique historical source spelling.

FeeConfig deserialization is gated by allocation: the normal schedule is read at
2,512 bytes, the stable schedule at 4,073, and exotic flat fees at 4,097. Earlier
layouts default the absent fields to empty/zero. Tests compare these boundaries
for both queries and writes; adding stable/exotic field bytes to a legacy
allocation does not make the original decoder consume them.

The three configuration setters have 625 independent SBF cases. Schedules must
contain 1–50 strictly increasing thresholds and each fee sum must be at most
10,000 basis points. Addition overflow aborts in the original and candidate.
The normal updater validates flat fees before schedule checks. Exotic fee updates
grow older accounts to 4,097 bytes and top up rent only when growing. State,
events, CPI payloads and rollback are compared, including preservation of the
existing schedule in current layouts. These are bounded reconstruction checks,
not proof that every configuration transition is safe.

Permissionless `extend_fee_config` validates the discriminator, owning program and
stored-bump PDA with custom error 6028, without decoding fee vectors. Accounts of
at least 4,097 bytes are left unchanged. Smaller accounts grow with zero-filled
bytes and a System transfer equal to the difference between old/new rent minima,
even when already overfunded; 297 cases compare this behavior and event CPI.
`revoke_fee_sharing_authority` and `transfer_fee_sharing_authority` are deprecated
in the captured deployment. Their recovered dispatches always return 6023;
80 payload/account-shape cases pass. They count as implemented rejection paths,
not recovered historical successful authority-transfer functionality.

The two tier upserts overwrite from the supplied offset, append beyond the old
end and retain unaffected trailing tiers. Offset cannot exceed the old length;
combined size cannot exceed 50. Validation covers the entire resulting schedule,
including retained entries. Their 578 cases cover insertion, overwrite, gaps,
length/order/fee boundaries and legacy allocation behavior. Events carry the
incoming tiers and offset. `update_admin` has 56 cases, accepts any new key,
including zero and nonsigners, and emits the previous and new keys. Its acceptance
of zero differs from the FeeProgramGlobal authority setter; these are separate
configuration types and recovered behaviors.

Donation creation and forwarding are integrated from the independently validated
draft (formerly `localnet/recovery/fees-donation/README.md`, removed from the tree). Their 713 signed synthetic
cases pass against this combined executable. A further 10-step persistent
creation/deposit/crank sequence and 10 Surfpool comparisons pass with normally
verified test-owned signatures. The sequence compares exact timestamped events;
independent Surfpool processes exclude only `last_crank_ts` wall-clock differences
from state equality and retain the raw values. Captured external dependency
binaries execute locally; the donation relay source remains unrecovered.

The three social-fee handlers add 1,562 signed differential cases, comparing
state, errors, events, CPI instructions and optional claim return values. The
prior retained executable also passes 29 Surfpool comparisons (58 signed
transactions) for social creation, SOL claims and token claims. See the
social recovery notes (formerly `localnet/recovery/fees-social/README.md`, removed from the tree) for the
179-byte rent reserve, cooldown, versioned initialization, saturating counters,
token ATA creation and precise timestamp exclusions. These observations do not
establish that every authorization or token-extension combination is safe.

The withdrawal token-option checks now convert `FeeError::IncompleteTokenAccounts`
only on the missing-option branch, with no source-origin attachment. Complete
original and candidate application bodies support the three ordered checks and
the owned enum-conversion role; the complete converter matches after call/address
normalization. The existing cases directly cover missing vault and user application errors;
the final missing-token-program application error is supported statically but is
not reached by these fixtures. Earlier option checks or account constraints win.
These cases do not measure allocations or prove whole-handler cleanup equivalence. The previous
V2 caller checkpoint (formerly `repro/pump_fees/v2-caller-v144/README.md`, removed from the tree) is retained.

Referral `withdraw` adds 113 signed differential cases and 16 independent Surfpool
comparisons. It authenticates the user signer and the System-owned referral PDA,
retains the zero-data rent minimum for SOL, and supports optional token withdrawals
with mint/authority/program checks but no ATA-address requirement. The retained
prior v1.44 executable passes all 55 donation/social/withdraw Surfpool comparisons
(110 signed transactions), plus the separate persistent donation sequence. See
withdrawal recovery (formerly `localnet/recovery/fees-withdraw/README.md`, removed from the tree).

External Pump Global/BondingCurve and AMM Pool types now use generated Anchor account
codecs with explicit external owners. Sharing and donation parsing reuse the same
AMM Pool type. At the earlier external-codec checkpoint, three complete checked
decoder patterns differed from the captured original only in embedded source-file
length and source-line constants after relocation/call masking. Nine
ordinary-signature malformed-account checks and all existing regressions passed;
this did not establish whole-program identity. See
codec evidence (formerly `repro/pump_fees/external-codecs-v144/README.md`, removed from the tree).


## Declared external programs and workspace layout

At the retained declared-program checkpoint, Pump `Global`/`BondingCurve` and
PumpSwap `Pool` were generated by consecutive `declare_program!` invocations at
`programs/pump-fees/src/lib.rs:27` and `:28`,
using the retained public historical IDLs under `idls/`. The workspace root owns
this member's manifest profile and lockfile; other reconstructed crates keep their
own workspace boundaries. Moving the existing macro items after `declare_id!`
requires no padding or extra source lines. The preceding reconstructed imports
and modules are not asserted to be the historical source prefix.

At that checkpoint, the three complete 728-byte checked decoders match the captured instruction
patterns after call/relocation address normalization, with identical relocation
patterns and all seven internal calls mapped consistently. Filename and line
literals are checked separately. Raw function bytes and the complete ELF still
differ. Nine malformed-account cases also reproduce the exact Anchor error lines,
including filename and line. This does not prove a unique original macro, IDL
revision, compiler or historical source tree.

The retained declared-program candidate is 766,800 bytes with SHA-256
`cf34104a46c65538e7de734abfa9d5d74102639257969cc4e51eb36a31cbd0eb`.
The declared-program evidence (formerly `repro/pump_fees/declared-programs-v144/README.md`, removed from the tree)
retains whole-workspace/IDL inputs, the actual build helpers, bounded decoder
comparisons, all 17,372 comparison receipts and the ten-step donation sequence.
It preserves the earlier helper used for the isolated experiment separately from
the corrected two-file helper used for the main build. Whole-file byte equality
remains false, and the older Surfpool receipts are not reattributed to this ELF.

## Recovered guard and account-layout details

Three buyback guards use `require_gt!(8u8, index, InvalidBuybackIndex)` and the
shared update context boxes its vault account. Their instruction bodies and
value-formatting helper support these source choices, and nine normally signed
index-7/8/255 comparisons assert exact compared-value logs. The separate
buyback checkpoint (formerly `repro/pump_fees/buyback-source-v144/README.md`, removed from the tree) retains
the controlled macro, integer-type, and account-layout builds.

`set_authority` uses a plain public-key inequality guard. Unlike
`require_keys_neq!`, it does not attach compared-key fields to `InvalidAdmin`,
matching the original error dataflow and logs. Its 3,320-byte body has the
original relocation pattern and fourteen mapped internal calls; after address
normalization, only source filename length and line constants differ.

The authority-guard checkpoint (formerly `repro/pump_fees/authority-guard-v144/README.md`, removed from the tree)
retains the clean main build, its exact scratch identity, all 22 source/workspace/IDL
inputs, and 17,384 comparison receipts plus the donation sequence. Its ELF is
768,824 bytes, SHA-256
`952a96cdb974517ec85ebeff3e2b5ec690029aaf3f822dfc22501e95bc3dba66`.
Source locations, compute-unit consumption and the complete executable still
differ from the capture; these checks do not establish unique historical source.


## Social claim v2 account layout

`ClaimSocialFeePdaV2` boxes its quote mint and uses by-value `AccountInfo` fields for event authority and program, preserving the existing account constraints. The original parser's field stores and generated event-CPI account contract support these types. Together they reproduce the complete 560-byte normalized account-exit body, seven direct callee bodies and three bounded literal spans. Boxing alone left one context offset unmatched; that earlier attempt remains preserved.

This source-layout result does not prove recursive data/call closure, original whole-file identity or a completed audit. The historical social v2 layout checkpoint (formerly `repro/pump_fees/social-v2-account-layout-v144/README.md`, removed from the tree) retains the 770,624-byte `c181b0ba75aee67369385e04908d89088552c1fad756bf5a21d7fb21979e6a58` ELF and its own fresh receipts. The current legacy-caller checkpoint above carries freshly executed scratch receipts by whole-file identity and retains the inline initializer and social exit checks.

At the preceding legacy-value checkpoint, the payout mismatch was changed to
formatted compared values through
`Error::with_values`, matching the original owned-string payload contract.
Availability, key equality, error code, filtering, payout and authorization
order were preserved. That checkpoint had four inlined formatting call sites
to the original's raw-identical 40-byte Pubkey formatter, 17,461 passing
comparisons and a passing ten-step sequence. Its 585/562 inventory had
448/135/2 original dispositions; complete helper/handler CFG identity,
source coordinates and transitive data remain unresolved. No new cases or
whole-original byte equality are claimed. The preceding legacy-caller package
retains its original executable and evidence.

## V2 caller reconstruction

The current V2 body preserves the original ordering of version/authorization,
quote admission, remaining-account preprocessing and AMM V2 CPI. It selects
zero/nonzero stored-quote payout preparation, filters executable shareholders,
rescales retained weights, serializes changed sharing state before Pump, and
skips Pump when the prepared account list is empty. The Pump V2 call passes
initialize_ata=true; final shareholder validation and event emission follow.
The retained Pump V2 IDL entry supplies its generated client. No account context,
dependency, compiler, runtime assertion or fixture changed.

Five previously unattributed original windows now have complete normalized
matches: the called formatted-value helper, Pump V2 CPI, shared V2 info builder
and both V2 meta builders. Both payout helpers call the matched formatted-value
function. Matching CPI/meta/info roots also retain matching immediate targets.
These results do not establish full caller/parser/cleanup/data equivalence or
historical source identity. All 17,461 existing comparisons, including the
417 sharing rows, and the ten-step sequence pass for the new executable.


## Sharing creation optional-pool error

The first graduated-path pool check now passes the fieldless
`FeeError::AmmAccountsRequiredForGraduatedCoin` to `ok_or`, converting it to an
owned Anchor error only on the missing path. This removes the unsupported source
origin and successful-path owned-error allocation at that one site. The fresh
candidate branches on the pool marker before calling the complete converter,
which matches the original under call/address and relocation normalization.

That one-line correction did not resolve the raw four-word graduation decision.
The later graduation checkpoint below resolves its reserve predicate; repeated
optional pool/program/event ordering remained unresolved at that checkpoint. Whole sharing-handler,
parser, cleanup and recursive data equivalence remain open. The unchanged
17,461 comparisons and separate ten-step sequence are preservation evidence;
no case was added. Raw diagnostic differences remain in the checkpoint.
The prior withdrawal checkpoint (formerly `repro/pump_fees/withdraw-owned-error-v144/README.md`, removed from the tree)
remains immutable, including its missing-token-program coverage limitation.


### Graduation predicate checkpoint

The `graduation-zero-v144` checkpoint changes only sharing creation's graduation predicate to require all four decoded reserves to be zero, matching the original full parser-to-application field trace. The accepted first missing-pool enum conversion remains. The repeated optional pool/program/event ordering remained unresolved at that checkpoint; the later option-order checkpoint below addresses it.

The pinned v1.44 build and v1.52 strip use the same 26 source inputs apart from this predicate. See `repro/pump_fees/graduation-zero-v144/` for complete original/current function, call and data inventory, source bindings, unchanged finite runtime receipts and retained diagnostics. Main identity, when accepted, is recorded separately in `repro/pump_fees/graduation-zero-main-v144/`. These observations do not establish full original executable or application identity.


### Sharing option-order checkpoint

The `sharing-option-order-v144` checkpoint moves the AMM program and event presence checks to the original late position. After both Pump calls, the graduated path checks pool, updates and serializes sharing state, then checks program and event using fieldless enum19 conversions before AMM calls. The nongraduated path no longer performs the unsupported second state rewrite/exit. The accepted first pool conversion and all-four-reserves-zero predicate are unchanged.

See `repro/pump_fees/sharing-option-order-v144/` for exact source and original/candidate call/data evidence, unchanged finite runtime receipts and retained diagnostics. `repro/pump_fees/sharing-option-order-main-v144/` records the separately accepted main build identity. Complete original, recursive CPI, allocator and cleanup identity remain unproved.


### First Pump extension typed CPI checkpoint

The `sharing-pump-extend-v144` checkpoint restores only sharing creation's first Pump extension to the generated Anchor CPI helper. The local Pump IDL marks this extension's user writable, preserving the original and preceding manual-call metadata. The full emitted helper, AccountMeta constructor and AccountInfo constructor match their original instruction windows under call/relocation normalization, with all immediate target bodies supported. Remaining three manual calls are unchanged.

See `repro/pump_fees/sharing-pump-extend-v144/` for source/IDL bindings, complete before/after inventories, unchanged finite runtime receipts, signatures and raw diagnostics; the separate main identity is in `repro/pump_fees/sharing-pump-extend-main-v144/`. This does not claim whole original ELF equality or recursive target-program semantics.


## Second Pump CPI ownership checkpoint

The second Pump CPI checkpoint (formerly `repro/pump_fees/sharing-second-pump-cpi-v144/README.md`, removed from the tree)
restores the generated `migrate_bonding_curve_creator` CPI with its natural
CpiContext ownership, account-info append and data allocation. The local IDL
already has the original metadata; only one source call changes. Both existing
Pump calls keep their order and success barriers. The two remaining AMM manual
calls are unchanged.

The scratch candidate is `466725afe7406860177df56696a60897874ffa6dab7429e5cc62da087dbf48b5`.
The new complete CPI helper and AccountMeta constructor match normalized original
windows with their immediate call targets; the prior three helper matches remain.
The full inventory leaves 125 unattributed and two conflicting original windows.
All 17,461 unchanged comparisons and the separate ten-step sequence pass; no
new fixture or unique case is claimed. Raw diagnostics and full recursive/whole
original equality remain unresolved. The main companion (formerly `repro/pump_fees/sharing-second-pump-cpi-main-v144/README.md`, removed from the tree)
binds one clean main build to the tested scratch executable and symbols.


### Complete sharing-create typed CPI checkpoint

The `sharing-fourth-cpi-v144` checkpoint composes the reviewed third AMM extension and final AMM creator-migration typed APIs over Fee21. The fourth-call immediate baseline is the frozen third source; only sharing.rs changes from that baseline. Relative to Fee21 root, sharing.rs and the third-call AMM IDL writable-user field change. All four calls now use typed generated CPI contexts. Eight complete helper/metadata/info windows match originals under retained normalization; immediate target-body support is not recursive target-program proof.

See `repro/pump_fees/sharing-fourth-cpi-v144/` for exact layered source, full inventories, unchanged receipts, signatures, diagnostics and retained third-build helper transition history. Separate accepted main identity is in `repro/pump_fees/sharing-fourth-cpi-main-v144/`. Fourth build uses the restored accepted helper with explicit v1.44 and existing v1.52 strip; third's earlier failed global gate remains separately documented.


### Sharing creator/admin authorization checkpoint

The `sharing-authorize-v144` checkpoint restores original sharing creation authorization: the payer may equal Global.admin_set_creator_authority or the selected curve/pool creator. Required pool validation precedes authorization; existing sharing version returns early. Failure uses plain source-bearing6016 without compared-key payload. Eight typed CPI helper matches remain retained.

The unchanged17461 comparisons (focused20 included) and separate10steps pass; saved signatures are verified. Existing116sharing cases have zero payer/globaladmin matches, so the newly corrected admin-only domain remains static-only. No authority probe/newfixture was added. Full evidence and limits are at `repro/pump_fees/sharing-authorize-v144/`, with independent main executable/symbol identity at `repro/pump_fees/sharing-authorize-main-v144/`. Whole original/recursive behavior identity remains unproved.
