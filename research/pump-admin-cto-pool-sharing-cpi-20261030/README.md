# Pump Main `admin_cto`: pump_amm pool and pump_fees sharing-config CPI branches (original vs rebuild)

## Question

`admin_cto` is the community takeover that replaces a bonding curve's creator. After validation, it has three branches that involve other programs. Do the original Pump Main image and the rebuild behave the same on them, and do they build the same CPI instruction bytes?

1. **Sharing branch.** The curve's creator is the mint's pump_fees sharing-config PDA, and that account is owned by pump_fees and non-empty. Pump CPIs `pump_fees.admin_cto_sharing_config(Option<Pubkey>)` and keeps the sharing PDA as the curve creator.
2. **Shared-vault sweep.** A holder-reward conversion of such a curve sweeps the shared creator vault into the creator vault of the holder-rewards PDA. It checks the holder vault's seeds, the frozen state of the AMM coin-creator vault ATA, and that ATA's balance.
3. **Pool branch.** The canonical pump_amm pool PDA (index 0, pool-authority, mint, the curve's quote) is owned by pump_amm and non-empty. Pump CPIs `pump_amm.admin_cto_pool(target, is_holder_reward, Option<u64> fee)`.

The separate packet `pump-admin-cto-validation-boundaries-20261030` covers the validation layer, but none of its cases has a pool or a sharing config, so every success there ends on the curve-only path. The repository harness `scripts/pump_admin_cto_differential.py` imports `scripts/pump_validate_admin.py`, which reads a `research/imported-lab/...` snapshot that is not in the git tree.

## Setup

The setup is the same as in the validation packet:
- The Pump image is loaded with the upgradeable-loader layout in an in-process LiteSVM (solders 0.27.1).
- The pump_amm and pump_fees program ids hold the same in-memory no-op SBPFv0 program (`noop_stub()` in producer.py). The CPI instructions Pump builds (program, accounts, data) are therefore recorded in `inner_instructions` and compared byte for byte, while the callee side is not exercised.
- System, SPL Token and ATA are LiteSVM built-ins.
- Global is synthetic (1,088 bytes, with `admin_set_creator_authority` = fee payer) and so is the BondingCurve (166 bytes).
- The pool and sharing-config accounts are synthetic: zero-filled data of the stated size and owner.
- Keys come from fixed seeds, the clock is fixed, and there is no network.

| image | sha256 | bytes |
|---|---|---:|
| original `evidence/original/pump/deployed.so` | `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d` | 10,485,715 |
| rebuild `<candidate.so>` | `e04e3e5652e0cfbf55c6ef30533aea6084ea60432aac8a468056b0a6f19dd633` | 1,934,648 |

The rebuild was built with `scripts/build_partial_candidate.py` (platform-tools v1.44 / cargo-build-sbf 2.1.21) from source tree `97a2a2a383ba1bc5c5af08429de150e6124f0fc1` (repo commit `aba9e07e8872a53ebfdeffc7cc5bfa20714fc053`).

## Result

**All 27 cases behave identically on the original and the rebuild:** 0 behavior mismatches and 0 outcome mismatches. 20 cases succeed and 7 stop with the same error on both images. Compute units differ in all 27.

| group | cases | orig - rebuild |
|---|---:|---|
| successes that make the `admin_cto_pool` CPI only | 5 | −8 .. +7 |
| successes on the curve-only path (no CPI) | 8 | −2 .. +12 |
| successes with the sharing CPI and no sweep (`share/new-creator`, `share/and-pool`) | 2 | +7, +2 |
| successes through the shared-vault sweep | 5 | +32 .. +42 |
| `require!` stops (`CtoNewCreatorRequired` l.306, `CreatorShouldNotBeZero` l.307, `CreatorFeeBpsOutOfRange` l.338, sweep `ConstraintSeeds` l.648, `CtoSharedVaultFrozen` l.660) | 6 | +28 .. +45 |
| `InvalidCreator` admin_cto.rs:312 (new_creator = sharing PDA) | 1 | **+137** |

- Every error stop also differs in the AnchorError source path (`programs/pump/src/...` vs `src/...`, same line).
- The `InvalidCreator` +137 matches the +136 at the same line in the validation packet.
- The sweep path costs the original 32–42 CU more on every successful case that goes through it. This packet does not locate where inside `sweep` the difference arises.

## Behavior the cases pin down (identical on both images)

1. **Pool gate.** `admin_cto_pool` is called when the pool PDA is owned by pump_amm and has at least 1 byte of data.
   - 0 bytes, a system-owned address and a pump_fees-owned address all take the curve-only path, which logs "No canonical pump pool for this mint; curve only".
   - The pool seeds use the curve's quote mint, so on a token-quote curve a WSOL-quote pool is not found (`pool/tq-wsol-pool-only`).
2. **Pool CPI payload.** The payload is `target` + `is_holder_reward` + `Option<u64> fee`. The target is the new creator, or the holder-rewards PDA on a holder conversion, and the fee is passed through as `Some(100)` or `None`.
3. **Sharing gate.** The curve counts as shared only when its creator equals the sharing PDA **and** the account is owned by pump_fees **and** has data. With no data, a pump-owned account, or a missing account, the handler treats the sharing PDA as an ordinary creator: curve-only, with "Creator is not a system-owned wallet; fees left in the vaults" when the account exists.
4. **Sharing CPI payload.** With a new creator it is `Some(NEWC)`, and the curve creator **stays** the sharing PDA (event `new_creator` = sharing PDA, `sharing_config_reset` = 1). On a holder conversion it is `None`. When a pool also exists, both CPIs are made: first sharing, then pool. The pool target is the sharing PDA, or the holder PDA on a conversion.
5. **Sweep.**
   - The holder vault slot must be `creator-vault(holder-rewards PDA)`. Passing the holder-rewards PDA itself stops with `ConstraintSeeds` (l.648).
   - A frozen AMM coin-creator vault ATA holding 5 stops with `CtoSharedVaultFrozen` (l.660). Holding 0, it passes.
   - A non-frozen ATA holding 5 adds a CPI to `pump_amm.transfer_creator_fees_to_pump_v2` before the sharing CPI.
   - A native creator vault funded 1,000,000 above rent is swept (`swept_to_holder_vault` = 1,000,000).
6. `new_creator = sharing PDA` is rejected with `InvalidCreator` (l.312). A missing `new_creator` (`CtoNewCreatorRequired`) and the default key (`CreatorShouldNotBeZero`) are rejected on shared curves as on plain ones.

## Reproduce

```
python3 producer.py --root <repo> --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}' --out .
python3 verify.py --images '{"original": "<deployed.so>", "candidate": "<candidate.so>"}'
```

`producer.py` is deterministic: two runs produced byte-identical `runtime/` files. `verify.py` does three things:
- It checks both image hashes against the report.
- It replays all 27 cases on both images from `runtime/plan.json.gz` and requires every receipt to match byte for byte.
- It recomputes the summary.

It reads no repository files and exits 0 on success, 1 on failure.

## Per-case results

| case | note | result (both images) | CU original | CU rebuild | orig - rebuild | error site (original / rebuild) |
|---|---|---|---:|---:|---:|---|
| `pool/new-creator` | AMM-owned pool, new_creator NEWC | ok:No creator fee to collect | 71899 | 71906 | -7 |  |
| `pool/no-new-creator` | AMM-owned pool, no new_creator | error:CtoNewCreatorRequired | 59643 | 59615 | +28 | `creator/admin_cto.rs:306` (`programs/pump/src/` / `src/`) |
| `pool/holder-convert` | AMM-owned pool, holder conversion | ok:No creator fee to collect | 71780 | 71785 | -5 |  |
| `pool/data-1-byte` | pool with 1 byte of data | ok:No creator fee to collect | 71898 | 71905 | -7 |  |
| `pool/empty-data` | AMM-owned pool with 0 bytes -> curve only | ok:No creator fee to collect / No canonical pump pool for this mint; curve only | 67486 | 67488 | -2 |  |
| `pool/system-owned` | pool address funded but system-owned -> curve only | ok:No creator fee to collect / No canonical pump pool for this mint; curve only | 67475 | 67477 | -2 |  |
| `pool/fees-owned` | pool address owned by pump_fees -> curve only | ok:No creator fee to collect / No canonical pump pool for this mint; curve only | 67475 | 67477 | -2 |  |
| `pool/tq-fee-100` | token-quote curve, pool for QUOTE, fee 100 | ok | 99647 | 99640 | +7 |  |
| `pool/tq-fee-0` | token-quote curve, pool, fee 0 | error:CreatorFeeBpsOutOfRange | 62826 | 62781 | +45 | `creator/admin_cto.rs:338` (`programs/pump/src/` / `src/`) |
| `pool/tq-holder-fee` | token-quote curve, pool, holder conversion with fee 100 | ok | 99509 | 99517 | -8 |  |
| `pool/tq-wsol-pool-only` | token-quote curve, only a WSOL-quote pool exists (wrong seeds) | ok:No canonical pump pool for this mint; curve only | 95223 | 95211 | +12 |  |
| `share/new-creator` | shared curve, new_creator NEWC | ok:No canonical pump pool for this mint; curve only | 69592 | 69585 | +7 |  |
| `share/no-new-creator` | shared curve, no new_creator | error:CtoNewCreatorRequired | 58019 | 57990 | +29 | `creator/admin_cto.rs:306` (`programs/pump/src/` / `src/`) |
| `share/new-default` | shared curve, new_creator default key | error:CreatorShouldNotBeZero | 58549 | 58517 | +32 | `creator/admin_cto.rs:307` (`programs/pump/src/` / `src/`) |
| `share/holder-convert` | shared curve, holder conversion, holder_creator_vault slot = holder-rewards PDA | error:ConstraintSeeds | 60914 | 60881 | +33 | `creator/admin_cto.rs:648` (`programs/pump/src/` / `src/`) |
| `share/holder-sweep` | shared curve, holder conversion, holder creator vault slot correct, vaults empty | ok:No canonical pump pool for this mint; curve only | 74650 | 74608 | +42 |  |
| `share/holder-sweep-vault-funded` | same, sharing creator vault 1,000,000 above rent(0) | ok:No canonical pump pool for this mint; curve only | 79181 | 79141 | +40 |  |
| `share/holder-sweep-amm-frozen-5` | AMM coin-creator vault ATA frozen holding 5 | error:CtoSharedVaultFrozen | 64112 | 64079 | +33 | `creator/admin_cto.rs:660` (`programs/pump/src/` / `src/`) |
| `share/holder-sweep-amm-frozen-0` | AMM coin-creator vault ATA frozen holding 0 | ok:No canonical pump pool for this mint; curve only | 75283 | 75241 | +42 |  |
| `share/holder-sweep-amm-5` | AMM coin-creator vault ATA (not frozen) holding 5 | ok:No canonical pump pool for this mint; curve only | 83479 | 83447 | +32 |  |
| `share/sharing-empty` | curve creator = sharing PDA but account has no data -> not shared | ok:Creator is not a system-owned wallet; fees left in the vaults / No canonical pump pool for this mint; curve only | 65133 | 65131 | +2 |  |
| `share/sharing-wrong-owner` | sharing PDA owned by pump -> not shared | ok:Creator is not a system-owned wallet; fees left in the vaults / No canonical pump pool for this mint; curve only | 65120 | 65118 | +2 |  |
| `share/sharing-absent` | curve creator = sharing PDA, account absent | ok:No creator fee to collect / No canonical pump pool for this mint; curve only | 65837 | 65838 | -1 |  |
| `share/not-creator` | sharing config exists but curve creator is CREATOR -> not shared | ok:No creator fee to collect / No canonical pump pool for this mint; curve only | 67475 | 67477 | -2 |  |
| `share/and-pool` | shared curve and AMM pool: both CPIs | ok | 74016 | 74014 | +2 |  |
| `share/and-pool-holder` | shared curve and AMM pool, holder conversion | ok | 79074 | 79036 | +38 |  |
| `share/new-is-sharing` | shared curve, new_creator = sharing PDA | error:InvalidCreator | 58102 | 57965 | +137 | `creator/admin_cto.rs:312` (`programs/pump/src/` / `src/`) |

### Successful cases: AdminCtoEvent and CPI payloads (original; rebuild identical)

| case | AdminCtoEvent (new_creator, holder, new_fee_bps, sharing_config_reset, swept_to_holder_vault, pool_updated) | CPIs to the pump_fees / pump_amm ids (payload decoded) |
|---|---|---|
| `pool/new-creator` | NEWC, 0, 0, 0, 0, 1 | admin_cto_pool(target=NEWC, holder=0, fee=None) |
| `pool/holder-convert` | holder-rewards PDA, 1, 0, 0, 0, 1 | admin_cto_pool(target=holder-rewards PDA, holder=1, fee=None) |
| `pool/data-1-byte` | NEWC, 0, 0, 0, 0, 1 | admin_cto_pool(target=NEWC, holder=0, fee=None) |
| `pool/empty-data` | NEWC, 0, 0, 0, 0, 0 | none |
| `pool/system-owned` | NEWC, 0, 0, 0, 0, 0 | none |
| `pool/fees-owned` | NEWC, 0, 0, 0, 0, 0 | none |
| `pool/tq-fee-100` | NEWC, 0, 100, 0, 0, 1 | admin_cto_pool(target=NEWC, holder=0, fee=100) |
| `pool/tq-holder-fee` | holder-rewards PDA, 1, 100, 0, 0, 1 | admin_cto_pool(target=holder-rewards PDA, holder=1, fee=100) |
| `pool/tq-wsol-pool-only` | NEWC, 0, 100, 0, 0, 0 | none |
| `share/new-creator` | sharing-config PDA, 0, 0, 1, 0, 0 | admin_cto_sharing_config(NEWC) |
| `share/holder-sweep` | holder-rewards PDA, 1, 0, 1, 0, 0 | admin_cto_sharing_config(None) |
| `share/holder-sweep-vault-funded` | holder-rewards PDA, 1, 0, 1, 1000000, 0 | admin_cto_sharing_config(None) |
| `share/holder-sweep-amm-frozen-0` | holder-rewards PDA, 1, 0, 1, 0, 0 | admin_cto_sharing_config(None) |
| `share/holder-sweep-amm-5` | holder-rewards PDA, 1, 0, 1, 0, 0 | transfer_creator_fees_to_pump_v2(0 B args); admin_cto_sharing_config(None) |
| `share/sharing-empty` | NEWC, 0, 0, 0, 0, 0 | none |
| `share/sharing-wrong-owner` | NEWC, 0, 0, 0, 0, 0 | none |
| `share/sharing-absent` | NEWC, 0, 0, 0, 0, 0 | none |
| `share/not-creator` | NEWC, 0, 0, 0, 0, 0 | none |
| `share/and-pool` | sharing-config PDA, 0, 0, 1, 0, 1 | admin_cto_sharing_config(NEWC); admin_cto_pool(target=sharing-config PDA, holder=0, fee=None) |
| `share/and-pool-holder` | holder-rewards PDA, 1, 0, 1, 0, 1 | admin_cto_sharing_config(None); admin_cto_pool(target=holder-rewards PDA, holder=1, fee=None) |
