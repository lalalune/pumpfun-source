# Scripts

Tooling for capturing deployments, building candidates, comparing them with the
captured originals and running differential tests in a local VM. Every Python
script here is listed below by purpose; a check mark means a GitHub workflow runs it
directly (others run as libraries of those steps or by hand). The non-Python files
(`pump_rustc_source_path_wrapper.sh`, `core_linux_v144_inputs.json`,
`pump_physical_source_wrapper.sh`, `pump_text_layout_rustc.sh`,
`pump_text_layout_linker.sh`,
`pump_text_layout_default.ld`, `pump_linux_v144_sbf_libraries.json`,
`pump_linux_v144_sbpf_libraries.json` and `supported_sbpf_policies/`) are inputs
to the build scripts.

The verified builder's three `.sh` compiler/link launchers use its selected
Python interpreter, including when `python3` is absent from `PATH`. The original
Python implementations remain separate hash-bound inputs. Launcher hashes and selected
interpreter paths participate in new verified dependency-cache keys and
seed admission; older cache entries are preserved and are not silently reused
under the changed route. See the [actual offline build controls](../research/verified-hook-interpreter-20261101/README.md).

## Conventions

The workflow input checker, `python scripts/check_workflow_inputs.py`, also needs
the pinned packages in `requirements.txt`: PyYAML supplies its `yaml` import.
Install those requirements in the selected Python environment before running it
or the workflow input regression suites.

For saved AMM verification on Windows or POSIX, run
`python -B scripts/verify_pump_amm_checkpoint.py` with the pinned packages in
`requirements.txt`. The current gate uses `amm_checkpoint_modules.py` to read the
sealed canonical and layout checkpoints. It checks each adapted module's original
SHA-256 and changes only manifest-key path serialization in memory to POSIX form.
The archived scripts, manifests, source inputs, compiler outputs and checks remain
intact; direct invocation of the archived verifiers retains their original
platform limitations. This is saved evidence verification, not a fresh build or
VM replay. Run its stdlib-only regressions with
`python -I -B scripts/test_amm_checkpoint_modules.py`.

The main Pump builder also accepts `--target sbpf-solana-solana` for an uncached
build with an installed native SDK. The default remains `sbf-solana-solana`.
An explicit target must agree with a selected target-library profile. Native
SBPF builds without a profile cannot use the dependency cache. Build receipts
record the selected target and its library hashes, and verify those libraries
remain unchanged through compilation.


- Run from the repository root with Python 3.12. Differential and Surfpool scripts
  need the pinned packages in `requirements.txt` (`solders==0.27.1`).
- Differentials take `--candidate <program.so>` and `--output <file.json[.gz]>`, load
  the captured original from `evidence/original/<program>/deployed.so` (Donation Relay:
  `evidence/dependencies/donation_relay/deployed.so`), run the same signed transactions
  against both in LiteSVM and report per-case results. Most write a `mismatches` list;
  a few use per-row `match` fields instead.
- `*_surfpool.py` scripts replay the same cases against a local Surfpool validator
  (formerly `localnet/`, removed from the tree). Nothing is sent to a live network.
- `*_fixture.py` modules build the synthetic accounts shared by a family of
  differentials. The Pump `*_probe.py` scripts record prerequisite observations
  without asserting equality; `fees_donation_crank_probe.py` is a full differential
  despite its name.

## Why the set is frozen

The pass-27 CI guard pins this directory: the exact set of 187 `scripts/*.py` files
and the SHA-256 of each one. Evidence packages formerly under `repro/` (removed from
the tree) also recorded the script hashes they ran with. Editing an existing script
needs a reviewed asset transition (formerly `repro/consolidation/2026-10-26/`,
removed from the tree) and must not change a script that an immutable checkpoint
verifier pins (for example `build_partial_candidate.py`). Adding, renaming or merging
scripts changes the pinned set itself and needs a new guard generation. New tooling
belongs in the evidence package that uses it, as the former
`repro/behavioral-recovery/scripts/` layout did.

## Core: capture, analysis, comparison

### Saved-capture checks on the current checkout

From the repository root, run:

```sh
python -E -X utf8 scripts/verify_evidence.py
python -E -X utf8 scripts/test_tooling.py
```

The saved-capture verifier uses explicit runtime checks, which remain active
under `-O`, `-OO` and `PYTHONOPTIMIZE`. The commands above use `-E` to keep the
invocation independent of inherited Python settings; `-X utf8` also lets the
tooling tests read the checked-in UTF-8 IDLs on Windows. These flags do not imply
that every other archived verifier supports optimized Python.
`python -X utf8 scripts/test_capture_verification_modes.py` exercises the saved
capture CLI on owned corpus copies in all five optimization modes, including
rejection of altered payloads and capture metadata.
These commands verify saved evidence and comparator behavior, not a source
rebuild or runtime equivalence. The previously recommended
`research/evidence-checks-optimized-python/` package is absent from this checkout;
do not treat that historical package path as an installed entrypoint.

| Script | CI | Purpose |
| --- | :-: | --- |
| `analyze.py` |  | Offline ELF layout, string provenance and public-interface inventory. |
| `build_source_manifest.py` |  | Hash local Rust, workspace, Anchor IDL and explicitly supplied build inputs. |
| `capture.py` |  | Read-only finalized RPC capture. Refuses replacing existing evidence. |
| `compare.py` |  | Compare a separately built artifact, including allocation padding; never copies code. |
| `disassemble.py` |  | Generate analyst disassembly, never a source rebuild or candidate executable. |
| `local_validation.py` | ✓ | Offline malformed-input smoke tests; not a functional or authorization audit. |
| `recover_dispatch.py` |  | Locate Anchor discriminator comparisons and wrapper calls in original SBF. |
| `verify_evidence.py` | ✓ | Saved-evidence implementation with explicit runtime checks. Use the [current local commands](#saved-capture-checks-on-the-current-checkout). This is NOT a rebuilt-source verification. |

## Builds, toolchains and dependency provenance

| Script | CI | Purpose |
| --- | :-: | --- |
| `build_fee_selection.py` |  | Compile recovered Rust independently, then compare one original function. |
| `build_partial_candidate.py` |  | Build an incomplete program from source and retain an honest whole-file comparison. |
| `build_quote_fees.py` |  | Build recovered two-crate quote-selection code; compare unmodified object bytes. |
| `build_quote_host.py` | ✓ | Build native recovered fee routing for original-versus-recovered tests. |
| `build_reconstruction_candidate.py` |  | Proposed routing: defaults/old overrides retain the frozen historical helper. |
| `build_supported_sbpf_candidate.py` |  | Proposed measured v1.53/v1.54 direct-Cargo adapter. Selects the supplied manifest's package explicitly; --dry-run never invokes tools. |
| `check_sbf_backend_diagnostics.py` |  | Reject reported backend errors even when Cargo returned zero; no runtime acceptance. |
| `core_linux_v144_build.py` | ✓ | Fixed-source Fees v1.44 compile and recorded v1.52 strip pipeline. |
| `measure_relay13_linux_v148.py` |  | SOURCE-ONLY PROPOSAL: one explicit Linux measurement, never a promotion tool. |
| `measure_relay_linux_v148.py` | ✓ | SOURCE-ONLY PROPOSAL: one explicit Linux measurement, never a promotion tool. |
| `prepare_locked_cargo_home.py` |  | Prepare an isolated offline Cargo cache from checksum-verified local archives. |
| `pump_analyze_ata_layout.py` |  | Read-only instruction correspondence analysis; never emits a transformed ELF. |
| `pump_build_constant_product.py` |  | Compile the arithmetic fragment unchanged and retain its measured byte mismatch. |
| `pump_build_token_dependency.py` | ✓ | Reproduce the pinned SPL Token verified-build recipe in its official Linux image. |
| `search_dependency_commit.py` | ✓ | Search upstream commits for the exact byte-identical build of a captured dependency. |

## Checkpoint and binding verifiers

| Script | CI | Purpose |
| --- | :-: | --- |
| `reconstruction_identity_audit.py` |  | Measure exact byte gaps without treating size similarity as source completeness. |
| `verify_current_bindings.py` | ✓ | Verify current tracked inputs; historical scratch paths use exact published copies. |
| `verify_current_checkpoint.py` | ✓ | Check immutable checkpoint evidence and actual current sources/helper provenance. |
| `verify_pump_amm_checkpoint.py` | ✓ | Verify selected AMM source and saved or fresh runtime receipts, including signatures. |
| `amm_checkpoint_modules.py` |  | Read sealed AMM source and packet inventories with portable path keys; archived bytes remain unchanged. |
| `verify_imported_lab.py` | ✓ | Verify frozen lab import and replay saved receipts in a disposable local tree. |
| `verify_mayhem_burn_sequence.py` | ✓ | Independently verify saved runtime receipts; no VM or network use. |
| `verify_mayhem_buy.py` | ✓ | Offline verification of saved signed buy receipts; never executes a VM or RPC. |
| `verify_mayhem_buy_v2.py` | ✓ | Offline verification of saved signed buy_v2 receipts; never executes a VM or RPC. |
| `verify_mayhem_pump_swap.py` | ✓ | Independent offline saved-receipt checks for both Mayhem PumpSwap trades; no VM or RPC. |
| `verify_mayhem_sell.py` | ✓ | Offline verification of saved signed sell receipts; never executes a VM or RPC. |
| `verify_mayhem_sell_v2.py` | ✓ | Offline verification of saved signed sell_v2 receipts; never executes a VM or RPC. |
| `verify_pump_compared_checkpoint.py` |  | Exact Pump compared-error checkpoint bridge; saved evidence only, no target/build. |
| `verify_pump_remaining_checkpoint.py` |  | Exact Pump compared-error checkpoint bridge; saved evidence only, no target/build. |
| `verify_pump_set_mayhem_params_8099.py` |  | Verify the merged-source synthetic Mayhem CPI receipt and builds. |
| `verify_pump_set_mayhem_params_synthetic.py` |  | Verify the saved local-only signed Pump Mayhem CPI differential receipt. |
| `verify_pump_source_path_remap.py` |  | Verify a controlled Pump-only Rust source-path remap build offline. |
| `verify_recovered_builds.py` | ✓ | Check saved partial-build provenance against current sources, artifacts and captures. |

## Tooling self-tests

| Script | CI | Purpose |
| --- | :-: | --- |
| `test_build_source_manifest.py` | ✓ | Regression checks for compiler inputs omitted by earlier build records. |
| `test_build_quote_fees.py` |  | Check a failed quote-selection compile step still leaves its build log; no compiler runs. Imported by `test_tooling.py`. |
| `test_amm_checkpoint_modules.py` | ✓ | Verify sealed AMM source mapping and rejection of source, workspace, module and packet drift. |
| `test_core_linux_pipeline.py` | ✓ | Synthetic preparation/provenance tests; no compiler, installer, tracer or network. |
| `test_core_linux_v144_retention.py` | ✓ | Focused synthetic file-inventory tests; never invoke build/main/download/run. |
| `test_fees_external_codec_cases.py` |  | Check each external-codec boolean case patches an IDL bool field, not the discriminator; runs inside `test_tooling.py`. |
| `test_localnet_sdk_plan.py` | ✓ | Fixture/argv tests only. No validator or transaction is executed. |
| `test_reconstruction_build_selection.py` | ✓ | Check the research wrapper preserves experiments and frozen-helper integrity. |
| `test_reconstruction_identity_audit.py` | ✓ | Guard exact-byte audit against allocation masking and silent stale fallback. |
| `test_sbf_backend_diagnostics.py` |  | Regression cases for zero-exit backend errors; no compiler or VM. |
| `test_supported_sbpf_policy.py` | ✓ | Run installed adapter fixtures and explicit Cargo entry-path escape regressions. |
| `test_tooling.py` | ✓ | Mutation tests ensuring the byte comparator cannot hide code/padding changes. |

## Runtime preparation for CI suites

| Script | CI | Purpose |
| --- | :-: | --- |
| `prepare_fees_withdraw_runtime.py` | ✓ | Extract the sealed, unchanged focused Fees harness for current-artifact CI. |
| `prepare_pump_nested_runtime.py` | ✓ | Copy the sealed nested-route harness and bind it to the current main build. |

## Pump differentials, validators and fixtures

| Script | CI | Purpose |
| --- | :-: | --- |
| `pump_admin_cto_differential.py` | ✓ | Pump admin_cto reconstruction comparisons with genuine captured dependency CPIs. |
| `pump_admin_token_incentives_differential.py` |  | Signed offline Pump admin incentive scheduler target/candidate comparison. |
| `pump_admin_token_incentives_verify.py` |  | Independent signed offline replay of Pump incentive scheduler evidence. |
| `pump_buy_v2_differential.py` | ✓ | Normally signed, synthetic offline buy_v2 / buy_exact_quote_in_v2 recovery. |
| `pump_cashback_accept_differential.py` |  | Differential for the is_cashback_coin branch of pump's v3 trade handlers. |
| `pump_cashback_differential.py` | ✓ | Offline ordinary-signer cashback accounting reconstruction fixtures. |
| `pump_claim_token_incentives_8099_verify.py` |  | Verify the 8099031-source claim build and signed offline differential. |
| `pump_claim_token_incentives_differential.py` |  | Signed offline Pump claim_token_incentives target/candidate differential. |
| `pump_claim_token_incentives_verify.py` |  | Re-execute and verify the signed Pump token-incentive claim differential. |
| `pump_create_control_differential.py` | ✓ | Offline creation reconstruction with ordinary mint and payer signatures. |
| `pump_create_differential.py` | ✓ | Offline creation reconstruction with ordinary mint and payer signatures. |
| `pump_create_nested_differential.py` | ✓ | Normally signed root creation followed by depth-one SOL-root nested creation. |
| `pump_create_nested_fixture.py` |  | Offline creation reconstruction with ordinary mint and payer signatures. |
| `pump_create_quote_differential.py` | ✓ | Offline creation reconstruction with ordinary mint and payer signatures. |
| `pump_create_v2_differential.py` |  | Offline creation reconstruction with ordinary mint and payer signatures. |
| `pump_creator_collect_differential.py` | ✓ | Offline normally signed creator collection differential fixtures. |
| `pump_creator_collect_v2_differential.py` | ✓ | Differential: Pump creator collect v2, candidate vs. captured original. |
| `pump_creator_distribution_differential.py` | ✓ | Direct normally signed Pump distribution after captured original sharing bootstrap. |
| `pump_creator_migration_differential.py` | ✓ | Normally signed creator migration after captured sharing bootstrap. |
| `pump_exact_quote_differential.py` | ✓ | Partial exact-quote v3 recovery with verified signatures and explicit synthetic state. |
| `pump_extend_differential.py` | ✓ | Normally signed local raw-account extension comparisons for captured Pump. |
| `pump_fee_sweep_differential.py` | ✓ | Differential: Pump fee sweep, candidate vs. captured original. |
| `pump_global_init_differential.py` | ✓ | Normally signed, offline Pump initialize differential fixture. |
| `pump_global_init_probe.py` |  | Offline, normally signed prerequisite probe for Pump initialize only. |
| `pump_holder_distribution_differential.py` | ✓ | Normally signed holder distribution comparisons against captured original. |
| `pump_holder_distribution_probe.py` |  | Local normal-signature holder fee payout fixture, no network writes. |
| `pump_idl_authority_differential.py` | ✓ | Offline Pump IDL-authority reconstruction with normal administrator signatures. |
| `pump_legacy_buy_differential.py` | ✓ | Offline legacy buy recovery: normally signed synthetic transactions, captured dependencies. |
| `pump_legacy_sell_configured_fee_differential.py` | ✓ | Extend frozen legacy sell fixtures with stored creator-fee overrides; no live RPC. |
| `pump_legacy_sell_differential.py` | ✓ | Offline legacy sell recovery: normally signed synthetic transactions, captured dependencies. |
| `pump_migrate_differential.py` | ✓ | Normally signed legacy Pump migration differential, synthetic state and captured CPIs. |
| `pump_migrate_probe.py` |  | Ordinary signed local legacy-migrate prerequisite probe; captured actual CPIs. |
| `pump_migrate_v2_differential.py` | ✓ | Normally signed Pump migrate_v2 differential, synthetic state and captured CPIs. |
| `pump_migrate_v2_probe.py` |  | Ordinary signed local migrate-v2 prerequisite probe; captured actual CPIs. |
| `pump_minimum_fee_differential.py` | ✓ | Differential: Pump minimum fee, candidate vs. captured original. |
| `pump_quote_control_fresh_differential.py` | ✓ | Offline original-vs-recovered differential tests for the Pump quote-control instructions. |
| `pump_sell_v2_differential.py` | ✓ | Normally signed, synthetic offline legacy sell_v2 recovery. |
| `pump_set_creator_differential.py` | ✓ | Normally signed synthetic Pump creator setter/metadata synchronization comparisons. |
| `pump_set_mayhem_params_signer_boundary.py` |  | Offline signer-boundary replay for Pump SetMayhemVirtualParams. |
| `pump_set_mayhem_params_synthetic_cpi.py` |  | Local-only Pump Mayhem-parameter differential through a synthetic Mayhem-ID CPI. |
| `pump_set_params_differential.py` | ✓ | Offline original-vs-recovered Pump administrative instruction differential tests. |
| `pump_trade_fixture.py` |  | Local captured-dependency sell-v3 fixture; initialization performs no RPC. |
| `pump_v3_configured_fee_differential.py` | ✓ | Configured creator-fee correction across three partial v3 handlers (SOL and synthetic USDC). |
| `pump_validate_admin.py` | ✓ | Offline original-vs-recovered Pump administrative instruction differential tests. |
| `pump_validate_all.py` |  | Run the published 44-suite bounded Pump corpus against one compiled ELF. |
| `pump_validate_authority.py` | ✓ | Offline original-vs-recovered Pump administrative instruction differential tests. |
| `pump_validate_buy.py` | ✓ | Compare the partial regular-SOL buy-v3 SBF path with the captured original. |
| `pump_validate_config_admin.py` | ✓ | Offline original-vs-recovered Pump administrative instruction differential tests. |
| `pump_validate_constant_product.py` | ✓ | Compare native recovered arithmetic with original sell-v3 reserve deltas. |
| `pump_validate_quote.py` | ✓ | Partial USDC-quote buy_v3/sell_v3 path vs. the captured original (synthetic quote mint and token accounts). |
| `pump_validate_sell.py` | ✓ | Compare the partial regular-SOL sell-v3 SBF path with the captured original. |
| `pump_validate_sell_accounting.py` | ✓ | Validate partial SOL sell accounting against original SBF event and state effects. |
| `pump_validate_volume.py` | ✓ | Validation: Pump volume accumulators, candidate vs. captured original. |
| `pump_verify_dependencies.py` | ✓ | Verify saved dependency registry evidence against captured binaries; no network. |
| `pump_volume_sync_differential.py` | ✓ | Pump synchronization: verified ordinary signatures and explicit synthetic state. |

## Pump Surfpool (signed local validator) runs

| Script | CI | Purpose |
| --- | :-: | --- |
| `pump_buy_v2_surfpool.py` |  | Normally signed offline Surfpool original/candidate Pump buy_v2 / buy_exact_quote_in_v2 checks. |
| `pump_cashback_surfpool.py` |  | Normally signed offline Surfpool claim_cashback / claim_cashback_v2 comparisons. |
| `pump_create_control_surfpool.py` |  | Normally signed offline Surfpool original/candidate Pump creation checks. |
| `pump_create_nested_surfpool.py` |  | Normally signed offline Surfpool original/candidate Pump creation checks. |
| `pump_create_quote_surfpool.py` |  | Normally signed offline Surfpool original/candidate Pump creation checks. |
| `pump_create_surfpool.py` |  | Normally signed offline Surfpool original/candidate Pump creation checks. |
| `pump_create_v2_surfpool.py` |  | Normally signed offline Surfpool original/candidate Pump creation checks. |
| `pump_exact_quote_surfpool.py` |  | Signed offline Surfpool partial exact-quote v3 purchase comparisons. |
| `pump_global_init_surfpool.py` |  | Normally signed offline Surfpool original/candidate Pump initialize checks. |
| `pump_holder_distribution_surfpool.py` |  | Signed offline Surfpool holder-distribution comparisons with captured CPI programs. |
| `pump_idl_authority_surfpool.py` |  | Normally signed offline Surfpool original/candidate Pump IDL authority checks. |
| `pump_legacy_buy_surfpool.py` |  | Normally signed offline Surfpool legacy buy / buy_exact_sol_in comparisons. |
| `pump_migrate_surfpool.py` |  | Signed offline Surfpool legacy migrate comparisons with captured CPI programs. |
| `pump_migrate_v2_surfpool.py` |  | Signed offline Surfpool Pump migrate_v2 comparisons with captured CPI programs. |
| `pump_v3_configured_fee_surfpool.py` |  | Signed offline Surfpool configured creator-fee v3 comparisons. |

## PumpSwap (AMM) differentials

| Script | CI | Purpose |
| --- | :-: | --- |
| `pump_amm_accumulator_differential.py` | ✓ | Local SBF account creation/closure differential, including signed system CPI. |
| `pump_amm_admin_differential.py` | ✓ | Local original/rebuilt PumpSwap administration differential tests; no RPC. |
| `pump_amm_boost_burn_differential.py` | ✓ | Offline original boost handler probes; synthetic state, normal test-owned signer. |
| `pump_amm_boost_differential.py` | ✓ | Local boost initialization and authentic signed migration differential. |
| `pump_amm_buyback_differential.py` | ✓ | Original/candidate SBF buyback configuration behavior, entirely in LiteSVM. |
| `pump_amm_cashback_differential.py` | ✓ | Differential: AMM cashback, candidate vs. captured original. |
| `pump_amm_collect_differential.py` | ✓ | Differential: AMM collect, candidate vs. captured original. |
| `pump_amm_create_differential.py` | ✓ | Local SBF pool creation differential; no RPC or network transactions. |
| `pump_amm_creator_reassignment_cto_differential.py` | ✓ | Normally signed local Pump admin_cto invoking PumpSwap through real CPI. |
| `pump_amm_creator_reassignment_differential.py` | ✓ | Normal-signature local PumpSwap creator reassignment differential; no RPC. |
| `pump_amm_extend_differential.py` | ✓ | Local raw-account extension differential. |
| `pump_amm_fee_config_differential.py` | ✓ | SBF fee configuration differential with boundary values and recipient constraints. |
| `pump_amm_incentives_differential.py` | ✓ | Synthetic AMM-owned fixtures, ordinary verified local transaction signatures; no RPC. |
| `pump_amm_legacy_buy_differential.py` | ✓ | Bounded AMM legacy buy/exact-quote with normal signed synthetic fixtures and captured CPIs. |
| `pump_amm_legacy_sell_differential.py` | ✓ | Offline AMM legacy sell with synthetic test-owned signer/state and captured CPIs. |
| `pump_amm_liquidity_differential.py` | ✓ | Local original/candidate SBF liquidity differential with captured SPL dependency ELFs. |
| `pump_amm_migration_create_differential.py` | ✓ | Saved signed migration replay using original Pump and captured dependencies. |
| `pump_amm_multi_hop_differential.py` | ✓ | Original AMM multi-hop observations with normally signed synthetic local state. |
| `pump_amm_reserved_differential.py` | ✓ | Original/rebuilt reserved-recipient administration; local SBF only. |
| `pump_amm_resize_differential.py` | ✓ | Original/rebuilt SBF global-config resize and system-CPI differential. |
| `pump_amm_reusable_harness.py` |  | Reuse compiled local SBF programs while restoring every case's account inputs. |
| `pump_amm_sweep_differential.py` | ✓ | Local protocol and creator fee sweep differential. |
| `pump_amm_trade_v2_differential.py` | ✓ | SBF v2 trading differential using captured token dependencies and fee-config state. |
| `pump_amm_transfer_creator_differential.py` | ✓ | Differential: AMM transfer creator, candidate vs. captured original. |

## Fees differentials and validators

| Script | CI | Purpose |
| --- | :-: | --- |
| `fee_recovery_fixture.py` |  | Synthetic local Pump Fees query fixtures. No RPC, signatures stay in LiteSVM. |
| `fees_admin_cto_differential.py` |  | Normally signed local Pump admin_cto invoking captured Fees through real CPI. |
| `fees_admin_differential.py` |  | Pump Fees administration: independent original/candidate local SBF execution. |
| `fees_admin_transfer_differential.py` |  | FeeConfig administration transfer with ordinary signatures and synthetic state. |
| `fees_buyback_differential.py` |  | Buyback differential: normal signatures and synthetic offline accounts; the candidate is optional. |
| `fees_config_differential.py` |  | Independent SBF fee-schedule mutations using synthetic authorized local state. |
| `fees_deprecated_differential.py` |  | Verify two deprecated dispatches reject all tested account/payload shapes. |
| `fees_donation_crank_probe.py` |  | Donation crank differential with a test-owned payer and synthetic offline state; reports mismatches. |
| `fees_donation_create_differential.py` |  | Recover donation-PDA creation with normally signed synthetic local transactions. |
| `fees_donation_sequence.py` | ✓ | Compare a persistent signed create/deposit/crank sequence in offline LiteSVM. |
| `fees_error_messages_differential.py` | ✓ | Compare two recovered error messages using normally signed offline fixtures. |
| `fees_extend_differential.py` |  | Permissionless FeeConfig resizing using normally signed offline transactions. |
| `fees_external_codec_differential.py` | ✓ | Check external-account decoder errors with normal offline test-owned signatures. |
| `fees_initialize_differential.py` |  | Compare FeeProgramGlobal initialization, including System CPI and rollback. |
| `fees_sharing_create_differential.py` |  | Differential: Fees sharing create, candidate vs. captured original. |
| `fees_sharing_update_differential.py` |  | Signed local sharing-update cases; original bootstrap precedes candidate load. |
| `fees_social_claim_differential.py` |  | Normally signed synthetic offline social fee claims, original/candidate comparison. |
| `fees_social_claim_v2_differential.py` |  | Normally signed local SocialFeePda v2 claim differential; the candidate is optional. |
| `fees_social_create_differential.py` |  | Signed synthetic local probes of original social-fee creation; no source claim. |
| `fees_upsert_differential.py` |  | Synthetic local fee-tier splice tests with actual admin signatures. |
| `fees_validate_all.py` | ✓ | Run all implemented Pump Fees handler suites against one candidate ELF. |
| `fees_withdraw_differential.py` |  | Normally signed offline referral withdraw differential; the candidate is optional. |
| `validate_fee_handlers.py` |  | Execute recovered query handlers and captured original independently in LiteSVM. |
| `validate_fee_selection.py` | ✓ | Differential-test the compiled Rust fragment against captured Pump Fees locally. |
| `validate_quote_fees.py` | ✓ | Compare recovered native quote-selection Rust against original SBF queries. |

## Mayhem differentials and fixtures

| Script | CI | Purpose |
| --- | :-: | --- |
| `mayhem_burn_sequence.py` | ✓ | Authorized sequential burns; genuine input bytes, ordinary signatures, no reset. |
| `mayhem_buy_differential.py` | ✓ | Unmodified original/candidate SBF comparison with ordinary signatures and synthetic accounts. |
| `mayhem_buy_fixture.py` |  | Original or source-built candidate ELF, signed synthetic accounts, local LiteSVM; never RPC. |
| `mayhem_buy_v2_differential.py` | ✓ | Unmodified original/candidate SBF comparison with ordinary signatures and synthetic accounts. |
| `mayhem_buy_v2_fixture.py` |  | Original or source-built candidate ELF, signed synthetic accounts, local LiteSVM; never RPC. |
| `mayhem_pump_swap_differential.py` | ✓ | Unmodified original/candidate SBF comparison with ordinary signatures and synthetic accounts. |
| `mayhem_pump_swap_fixture.py` |  | Ordinary signed synthetic Mayhem trade state with captured AMM/dependency ELFs; no RPC. |
| `mayhem_sell_differential.py` | ✓ | Unmodified original/candidate SBF comparison with ordinary signatures and synthetic accounts. |
| `mayhem_sell_fixture.py` |  | Original or source-built candidate ELF, signed synthetic accounts, local LiteSVM; never RPC. |
| `mayhem_sell_v2_differential.py` | ✓ | Unmodified original/candidate SBF comparison with ordinary signatures and synthetic accounts. |
| `mayhem_sell_v2_fixture.py` |  | Original or source-built candidate ELF, signed synthetic accounts, local LiteSVM; never RPC. |
| `mayhem_validate_admin.py` | ✓ | Local original-versus-rebuilt Mayhem admin instruction differential tests. |
| `mayhem_validate_extend.py` | ✓ | Differentially execute Mayhem's permissionless account extension path locally. |
| `mayhem_validate_fee_recipient.py` | ✓ | Compare original/candidate fee-recipient creation with captured CPI programs. |
| `mayhem_validate_quote_withdraw.py` | ✓ | Compare Mayhem quote withdrawals with captured token/ATA dependencies. |
| `mayhem_validate_sweeps.py` | ✓ | Differential tests of both Mayhem sweep paths using captured dependencies. |
| `mayhem_validate_withdraw.py` | ✓ | Compare complete Mayhem SOL admin withdrawal calls with the original. |

## Donation Relay

| Script | CI | Purpose |
| --- | :-: | --- |
| `donation_relay_differential.py` |  | Donation-relay original-vs-candidate differential oracle (LiteSVM). |
