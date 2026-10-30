# RESULT — bounded handler extensions for `pump.multi_hop_curve_swap` and `pump.create_v2`

Working session: local differential testing against the maintained checkout
`C:\Users\arzfeqsdeidm\Desktop\yop\AA\pumpfun-source-maintained` (HEAD `270d0178f43f557c16d7aad64b6bada691c4fd0c`,
parent `5bc20fe5`), runtime WSL Kali (python 3.13.12, `solders==0.27.1`, LiteSVM), all writes confined to
`work-handlers/`. No source file was modified (proof: `receipts/source_untouched.json`;
`git status --porcelain` empty, `git diff HEAD --stat` empty). No network access, no git mutation,
no stopped lane touched.

## 1. Modes chosen and why

### `pump.multi_hop_curve_swap` — one more hop level (three Pump curve hops)

Measured baseline of the retained coverage: the `native-curve-partial` suite drives **one** bonding-curve
hop group (5 remaining accounts) and the Tokenkeg suite drives **two** groups (SOL→A→B and B→A→SOL,
Pump CPI `hop_fees` length 2, 10 remaining accounts, 23 CPI accounts). (Some project texts call the
two-curve chains "three-hop", counting token movements; this report always states the measured
structure: number of hop groups / `swap_hop` iterations / `hop_fees` length.)

Chosen extension: **three consecutive Pump curve hop groups** per AMM `multi_hop_swap`
(SOL→A→B→C buys and C→B→A→SOL sells through the genuine captured AMM's PDA-signed CPI):
Pump CPI `hop_fees` length 3 (`[1,0,2]` buy / `[2,0,1]` sell), 15 remaining accounts (3×5),
28 CPI accounts, three `swap_hop` iterations, middle hop carrying fee gates **(0,0)** — a gate
combination the retained two-curve chains never produce. This is the mission's suggested
"un niveau de hops supplémentaire" and it extends the documented "arbitrary hop counts" gap by one
level using the existing canonical Tokenkeg fixture vocabulary (`base-fixture.json`,
retained curve/vault recipe). The native/WSOL alternative was not taken because the retained chains
already exercise the native curve at both endpoints; a native *middle* hop is unreachable through the
AMM's uniform-direction rule (only one curve exists per base mint), which is recorded as a limit.

### `pump.create_v2` — Mayhem mode with its quote-admission branch

Chosen over the Token-2022-ancestor mode because it is the best documented by existing evidence
(`scripts/pump_create_mayhem_differential.py`, the MAYHEM documents, the honest
`initialize_global_params` precondition construction), and the Token-2022 ancestor/extension area
borders the **stopped** old-V3 token-extension lane. The Mayhem **executable is the captured
original on both sides of every comparison**: the only variable is the Pump ELF. The stopped
`mayhem.initialize_mayhem_state` lane was not reconstructed or claimed; it is only *reached* as the
genuine pump→mayhem CPI target of the pump handler under test, exactly as the retained suite does.

## 2. Cases added and results (all cases executed; receipts saved)

### A. `packet/suites/pump_multi_hop_three_curve_differential.py` — 50 cases

Receipt `receipts/multi_hop_three_curve_cu14.json.gz` (explicit 1,400,000 CU budget):
**50/50 cases, zero mismatches** on `error, events, inner, return_data, before, after, pump_calls,
token_calls`; 18 original successes; 42 cases reach the Pump CPI; 100 verified outer signatures;
strict ordered logs equal excluding compute-meter lines (0 mismatches); repository diagnostic oracle
(`scripts/pump_diagnostic_audit.py`) 0 mismatches. Per-direction classes:

| class | cases/dir | result |
| --- | ---: | --- |
| positives: 4 fee modes (captured, exotic, flat-fallback, legacy-flat) × amounts 10^6, 10^9 | 8 | success on both sides, identical state/events/return |
| middle-curve cashback flag (`is_cashback_coin=1`, gates (0,0)) | 1 | success on both sides (new `validate_trade` branch) |
| amount = 1 boundary | 1 | 6041 `BuyNotEnoughSolToCoverFees` / 6022 `SellZeroAmount`, both sides |
| amount = 2^64−1 boundary | 1 | custom(1), CPI reached, both sides |
| final slippage `limit=2^64−1` | 1 | Pump completes, AMM `ExceededSlippage` rollback (6004) after successful Pump execution |
| zero input | 1 | AMM 6002 rejection before Pump (`pump_calls=0`) |
| truncated hop group (14 remaining) / extra partial group (18) | 2 | AMM 6044 `NotEnoughRemainingAccounts` before Pump |
| wrong user_out mint | 1 | AMM 6084 discontinuous-path rejection before Pump |
| middle-hop quote-mint mismatch (curve field 83:115) | 1 | Pump 6004 `MintDoesNotMatchBondingCurve` at hop 2 |
| middle curve `complete=1` (field 48) | 1 | Pump 6005 `BondingCurveComplete` at hop 2 |
| middle curve `is_mayhem_mode=1` (field 81) | 1 | Pump 6108 `MultiHopMayhemCurveNotSupported` at hop 2 via genuine CPI |
| substituted middle curve / substituted middle base vault | 2 | Anchor 2006 `ConstraintSeeds` at hop 2 |
| readonly middle quote vault | 1 | Anchor 2000 `ConstraintMut` |
| corrupted vault mint | 1 | Pump 6004 `MintDoesNotMatchBondingCurve` at hop-2 ATA admission (`buy_v2.rs:88`, same Source coordinate on both sides) |
| fee-config / pump-global discriminator zeroed | 2 | Anchor 3002 `AccountDiscriminatorMismatch` |

Receipt `receipts/multi_hop_three_curve_default200k.json.gz` (same 50 cases at LiteSVM's default
200,000 CU budget, `--compute-limit 0`): 30/50 match; **20 divergences, all in the cases that execute
all three hops** (16 positives + 2 slippage + 2 cashback): the *original* exhausts the compute meter
at hop 3 (`ProgramFailedToComplete` / `ComputationalBudgetExceeded`) where the candidate completes.
Cause proven in §3. This receipt is an observation of the compute artifact, not a semantic result.

`receipts/attempts/multi_hop_three_curve_attempt1_default200k.json.gz` is the retained discovery run
(48 cases, pre-correction script): it used curve offset 124 (`is_holder_reward`) instead of 81
(`is_mayhem_mode`) for the mayhem-flag mutation — a no-op mutation whose record shows the candidate
completing and the original hitting the meter; the corrected suite uses offset 81
(layout verified against `trade_types.rs`: disc 8 + 5×u64 → `complete`@48, `creator`@49:81,
`is_mayhem_mode`@81, `is_cashback_coin`@82, `quote_mint`@83:115, `depth`@141).

### B. `packet/suites/pump_create_v2_mayhem_mode_differential.py` — 28 cases

Receipt `receipts/create_v2_mayhem_mode.json.gz`: **28/28 cases, zero mismatches**; 7 successes
(Mayhem create through the genuine `initialize_mayhem_state` CPI, `global_params` duration 7,
name 32, **Mayhem + whitelisted quote mint**, **Mayhem + WSOL quote** (native normalization path
`quote_mint → default`), **holder-reward enabled** (creator becomes the `holder-rewards` PDA),
optional creator-fee arg 301); 21 negatives with identical errors on both sides, including the
targeted **`6071 MayhemModeQuoteMintNotAllowed`** from the configured-but-unlisted quote case
(the create_v2 line-758 branch is reached), 6063 `UnsupportedQuoteMint`, 6084
`HolderRewardDisabled`, 6082 `CashbackDeprecated`, 6030 `CreatorShouldNotBeZero`, 6048
`MayhemModeDisabled`, 6046 `CreateV2Disabled`, 2012 `ConstraintAddress` (wrong mayhem program id),
2006 `ConstraintSeeds` (wrong `global_params`/`sol_vault`/`mayhem_state`/`mint_authority`),
2000 `ConstraintMut` (readonly mayhem accounts), `MissingAccount` (bogus token vault),
custom(0) (pre-existing `mayhem_state`: double-init rejected by the genuine Mayhem CPI),
3005 `AccountNotEnoughKeys` (truncated accounts), 6043 `NameTooLong`. 112 verified outer signatures;
strict ordered logs equal excluding compute-meter lines; diagnostic oracle 0 mismatches.

## 3. Original/candidate divergence found — cause proven, no source change

The only observed behavioral divergence is the default-budget compute artifact described above.
`packet/tools/probe_compute.py` measures the retained two-curve case (identical AMM work and inputs)
with three Pump images (`receipts/compute_probe_two_curve.json`):

| Pump image | ELF bytes | pump-frame budget at CPI entry | AMM pre-CPI charge |
| --- | ---: | ---: | ---: |
| captured original (`evidence/original/pump/deployed.so`) | 10,485,715 | 112,228 | 87,772 |
| candidate stripped (maintained `builds/primary/candidate.so`) | 1,944,208 | 146,394 | 53,606 |
| candidate unstripped (same source, `builds/primary/unstripped.so`) | 2,678,152 | 143,458 | 56,542 |

Pre-charge deltas track the image size exactly: 8,541,507 B → 34,166 CU and 733,944 B → 2,936 CU,
both **250.0 bytes per CU** — an image-size-keyed runtime charge for the loaded executable, not
handler semantics. On top of it the original's handler logic runs slightly heavier (91,371 vs
87,555 CUs for the whole 2-curve CPI). At three hops the original needs ≈117k CUs of the 106,439 it
is granted at 200k total and stops at the meter; at 1,400,000 every case matches exactly, including
byte-identical hop events even in the truncated default-budget runs. **Conclusion: no semantic
divergence; no source correction is justified or made.** Making the candidate consume identical CUs
would require whole-binary identity, which remains open.

## 4. Window measurement (before/after)

Via `scripts/window_measure.py.measure()` between `evidence/original/pump/deployed.so` and the
**unstripped** symbol build `research/pump-program-creator-notice-qualification-20261028/artifacts/unstripped.so`
(symbol-indexed as required):

| receipt | total | normalized matched | raw matched |
| --- | ---: | ---: | ---: |
| `receipts/windows-before.json` | 1,035 | **1,019** | **188** |
| `receipts/windows-after.json` (no source change) | 1,035 | **1,019** | **188** |

No regression; no gain. Since no source byte changed, no rebuild was required and none was performed.

## 5. Suites executed (required + affected)

| suite | result |
| --- | --- |
| `scripts/verify_evidence.py` (required) | OK — 9 captures verified |
| `scripts/test_tooling.py` (required) | OK — 6 tests |
| `repro/pump/native-curve-partial-fortyeight/harness/pump_multi_hop_curve_differential.py` (affected: 56-case one/two-curve) | **56/56 passed** |
| `pump_tokenkeg_two_curve_differential.py` 20-case runtime replay (affected) | 20 cases, 16 original successes, 18 Pump-CPI cases, 40 verified signatures, 0 mismatches |
| `scripts/pump_create_mayhem_differential.py` (affected: pre-existing Mayhem suite; candidate-mayhem = captured original) | 17 cases, 0 mismatches |
| `scripts/pump_create_nested_differential.py` (affected: nested create) | 48 cases, 0 mismatches |
| `scripts/pump_create_quote_differential.py` (affected: create_v2 297-case) | 297 cases, 0 mismatches |
| new multi_hop three-curve (1.4M CU) | 50/50, 0 mismatches |
| new multi_hop three-curve (default 200k CU) | 50 cases, 20 compute-bound divergences (documented) |
| new create_v2 Mayhem mode | 28/28, 0 mismatches |

Tooling note (honest limitation, not a failure): `scripts/pump_tokenkeg_two_curve_differential.py`'s
`compiled_binding` gate compares the build report's `source_sha256` keys as ROOT-relative paths
(forty-eight-checkpoint report format). The current maintained candidate's actual build report
(`research/.../builds/primary/build-comparison.json`) deliberately retains executed staging prefixes
(`work/pump-cto-program-notice-fix-20261028/warm/source/...`), so that key-format equality can never
hold across the two packages. `packet/suites/tokenkeg_two_curve_runtime_replay.py` substitutes only
that binding function with the facts verifiable for the research-era report (attempt returncode 0,
`source_unchanged`, attempt/report source-hash identity, report candidate hash = actual candidate)
and records the limitation in the receipt; every runtime comparison of the wrapper is unchanged.
Verification: `receipts/check_build_binding.json`. The checkpoint's own canonical harness replay
already binds these 20 cases to a clean build.

## 6. Explicit limits (what this does NOT establish)

- `multi_hop_curve_swap`: hop counts beyond three curve groups, four-plus-hop chains, AMM-pool/curve
  mixed chains at the new level, native-curve *middle* hops (unreachable through the AMM's
  uniform-direction rule), other quote currencies, completion/migration, short-account resizing,
  Token-2022/extensions, holder/cashback (beyond the single flag variant) and Mayhem *modes* remain
  incomplete. `MultiHopHopFeesMismatch` is unreachable through the genuine AMM (it always emits valid
  gate bits) and remains untested. The mayhem-flag case proves only the fence rejection; the source
  domain fences are not claimed as original design intent.
- `create_v2`: the Mayhem branch is covered pump-side only with the captured Mayhem ELF; exhaustive
  ancestor/error coverage and Token-2022 ancestry/extension modes remain open. `mayhem.initialize_mayhem_state`
  itself remains a stopped lane and is neither reconstructed nor claimed here.
- No source change → no window movement (1,019/1,035 matched, 188 raw, unchanged). Whole meaningful
  ELF identity remains false; nothing here is a security review or a deployable replacement.
- Ordered-log equality holds only excluding complete runtime compute-meter lines (the strict-ordered
  policy); raw logs differ in compute lines because the images consume different CUs.
- The default-200k compute divergence is measured and explained, not fixed (fixing implies
  whole-binary identity). All synthetic starting states are explicitly synthetic; mainnet
  reachability is unproven. No signer/owner bypass, no fabricated case, no binary patch.

## 7. Exact commands

```sh
# environment (WSL Kali)
bash work-handlers/wsl/setup.sh                       # pip install --user solders==0.27.1 pyelftools jsonalias

# window measurement (before/after; unstripped symbol build as candidate side)
python3 work-handlers/wsl/measure_windows.py pumpfun-source-maintained/evidence/original/pump/deployed.so \
  pumpfun-source-maintained/research/pump-program-creator-notice-qualification-20261028/artifacts/unstripped.so \
  work-handlers/packet/receipts/windows-before.json baseline-maintained
python3 work-handlers/wsl/measure_windows.py pumpfun-source-maintained/evidence/original/pump/deployed.so \
  pumpfun-source-maintained/research/pump-program-creator-notice-qualification-20261028/artifacts/unstripped.so \
  work-handlers/packet/receipts/windows-after.json after-no-source-change

# new suites (from /mnt/c/Users/arzfeqsdeidm/Desktop/yop/AA)
python3 -B work-handlers/suites/pump_multi_hop_three_curve_differential.py \
  --candidate pumpfun-source-maintained/research/pump-program-creator-notice-qualification-20261028/builds/primary/candidate.so \
  --compute-limit 1400000 --output work-handlers/packet/receipts/multi_hop_three_curve_cu14.json.gz
python3 -B work-handlers/suites/pump_multi_hop_three_curve_differential.py \
  --candidate pumpfun-source-maintained/research/pump-program-creator-notice-qualification-20261028/builds/primary/candidate.so \
  --compute-limit 0 --output work-handlers/packet/receipts/multi_hop_three_curve_default200k.json.gz
python3 -B work-handlers/suites/pump_create_v2_mayhem_mode_differential.py \
  --candidate-pump pumpfun-source-maintained/research/pump-program-creator-notice-qualification-20261028/builds/primary/candidate.so \
  --output work-handlers/packet/receipts/create_v2_mayhem_mode.json.gz

# compute-cause probe and log audits
python3 work-handlers/wsl/probe_compute.py work-handlers/packet/receipts/compute_probe_two_curve.json
python3 -B work-handlers/wsl/audit_logs.py work-handlers/packet/receipts/log_audit.json \
  multi_hop_cu14=work-handlers/packet/receipts/multi_hop_three_curve_cu14.json.gz \
  multi_hop_default200k=work-handlers/packet/receipts/multi_hop_three_curve_default200k.json.gz \
  create_v2_mayhem_mode=work-handlers/packet/receipts/create_v2_mayhem_mode.json.gz

# required + affected suites (see packet/tools/run_affected.sh for the exact batch)
cd pumpfun-source-maintained
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
python3 repro/pump/native-curve-partial-fortyeight/harness/pump_multi_hop_curve_differential.py \
  --candidate research/pump-program-creator-notice-qualification-20261028/builds/primary/candidate.so \
  --output ../work-handlers/packet/receipts/affected/multi_hop_curve_partial.json
python3 scripts/pump_create_mayhem_differential.py \
  --candidate-pump research/pump-program-creator-notice-qualification-20261028/builds/primary/candidate.so \
  --candidate-mayhem evidence/original/mayhem/deployed.so \
  --output ../work-handlers/packet/receipts/affected/create_mayhem_preexisting.json.gz
python3 scripts/pump_create_nested_differential.py \
  --candidate research/pump-program-creator-notice-qualification-20261028/builds/primary/candidate.so \
  --output ../work-handlers/packet/receipts/affected/nested_create.json.gz
python3 scripts/pump_create_quote_differential.py \
  --candidate research/pump-program-creator-notice-qualification-20261028/builds/primary/candidate.so \
  --output ../work-handlers/packet/receipts/affected/create_v2_quote.json.gz
python3 ../work-handlers/suites/tokenkeg_two_curve_runtime_replay.py \
  --candidate research/pump-program-creator-notice-qualification-20261028/builds/primary/candidate.so \
  --output ../work-handlers/packet/receipts/affected/tokenkeg_two_curve_runtime_replay.json.gz
```

Candidate under test throughout: `builds/primary/candidate.so` = `artifacts/candidate.so`
SHA-256 `d0377d7cef5b7378063f8bfabac5dc9c08d29eeaaaaa14022d36909688ff5e1b` (stripped),
symbols `0f50faa8c325104dc77898ed84866dec2ad1eec475b6abba72c475cf7bf9bab6` (unstripped),
original Pump `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`.
`SHA256SUMS` covers every packet file.
