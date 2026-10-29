# Signed verification of the merged V3 Sell recovery

This packet independently rebuilds and replays the V3 Sell recovery merged in
[#1283](https://github.com/lalalune/pumpfun-source/pull/1283). **That PR receives
all source-recovery credit. This contribution changes no program source.**
It adds exact parent/merge build cohorts, signed differential receipts, an
immediate-callee audit, and portable verification in CI.

| Cohort | Git revision | Unstripped SHA-256 |
| --- | --- | --- |
| Control: exact merge parent | `1e9fe542bd25025409fb0827811655f28c1d62b5` | `e3410288eef8a18a76ded223f7bbc165bb693533029e6709e1088b1afa50f5df` |
| Candidate: merged #1283 | `e075a8ec15add21ed8ec07712e65d709a6e79db9` | `969811b0e0f673b693695ea651008cacd93eafa5a663dd8bec0e61d3b22d09a9` |

The branch is based on upstream `abd766d7a`; the two measured historical cohorts
above deliberately isolate #1283, excluding the subsequent Buy change #1281.
These are new warm builds of the exact Git-archived source revisions, not a claim
that every later checkout reproduces either image.

## Results

| Measurement | Parent | Merged recovery |
| --- | ---: | ---: |
| Sell bytes (original 6,032) | 6,040 | 6,040 |
| Existing instruction-alignment ratio | 0.950306 | 0.987066 |
| Original-only / candidate-only aligned instructions | 36 / 37 | 9 / 10 |
| Full Pump normalized / raw matches | 1,020 / 188 | 1,020 / 188 |
| Lost normalized / raw memberships | — | 0 / 0 |

Similarity is the existing `win.py` diagnostic, **not function completion**.
Sell (`0x14a8a8`) is still unmatched; the inventory remains 1,020/1,035.
#1283's two inline adapters retain typed mint references until both payment
calls have selected their native/token quote-account Options. The mint field
loads then match the original. Entry scheduling and the event-CPI Result/drop
tail remain different. No new recovery gain is claimed here.

- **117 existing configured-fee Sell cases, 351 signed executions** across the
  captured original and the two fresh builds have zero state, error, event,
  inner-instruction, return-data or ordered non-meter-log differences.
  Cases cover native SOL and synthetic SPL Token/Token-2022 quote accounts,
  creator-fee extremes, mode flags, zero creator and reserve boundaries.
  Existing case definitions are selected without edits. Transfer-fee extensions
  and exhaustive path coverage are not claimed.
- Only Sell's normalized body changes between the two cohorts. No named
  function is added or removed; all 1,035 normalized/raw memberships are checked.
  `.rodata` and `.data.rel.ro` are byte-identical between the rebuilt cohorts.
- All **47** actual direct-call/syscall edges resolve, in original order, to
  complete narrowly normalized immediate-callee bodies or exact syscall IDs.
  `audit.json` retains offsets and targets. This is not recursive/indirect-call
  or original pointed-to-data identity.
- The pinned macOS v1.44 SDK passed all 2,785 inventory entries, and all 25 Linux
  target-library hashes passed. The unchanged identity harness used the hybrid
  compiler, locked offline dependencies and `sbpf-solana-solana`. No SBF stack
  overflow warning occurred. Build `runtime_valid` means the warning check;
  executed runtime evidence is recorded separately. No cold/repeat-build claim.
- Root checks pass: `scripts/verify_evidence.py` (9 captures) and
  `scripts/test_tooling.py` (10 tests after rebasing onto `abd766d7a`).

The source archives retain all 63 Rust/manifest/lock inputs from each exact Git
revision; `source-inputs.json` binds the cohorts. Compiler outputs/logs, complete
official scores, the call audit, historical fixture and runtime receipts are
retained. The stripped runtime image hashes are in the build and replay records.
No matcher, toolchain, Cargo or emitted-byte modification is proposed.

## Reproduce

Use the setup in `reconstruction/README.md`, extract either source archive into
a scratch directory, then run the unchanged harness:

```sh
python3 reconstruction/harness/fastbuild.py --src SCRATCH/programs/pump --work WORK --out OUT
python3 reconstruction/harness/score.py OUT/unstripped.so --baseline reconstruction/pump-main/baseline/score.json
```

The local SDK/cache were under ignored `work/pump-v3-recovery/`; the runner set
its `SDK` path and `PUMP_RECON_HOME` accordingly. Compiler and target-library
bytes were unchanged. v1.44 `llvm-objdump` supplied symbols; v1.54 supplied only
disassembly text (v1.44 prints instruction indices rather than byte addresses).

Verify retained evidence without compiling or executing the VM:

```sh
python3 -m pip install solders==0.27.1
python3 reconstruction/pump-main/lanes/v3-sell-payment-layout/verify.py --signatures
```

The portable ELF reader is cross-checked against every v1.44 `llvm-objdump`
function entry in both images. The verifier recomputes every census membership,
compares the official reports, checks actual callees and re-compares runtime
receipts; `--signatures` independently verifies all transaction signatures.
`scorer.py` is an exact copy from tested upstream `60bdd8a7a`. Its narrow
normalizer is unchanged; the verifier parses original inputs freshly and does
not use its pickle cache. The packet is independent of cache-reader fix #1285.

Run `replay.py --control CONTROL.so --candidate CANDIDATE.so --output REPORT.json.gz`
with `solders==0.27.1` to execute the same 117 cases against the captured
dependencies. The historical fixture is recovered verbatim from
`6aa66f03c:research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json`.
Only its location is redirected when loading `scripts/pump_trade_fixture.py`.
This does not change fixture logic or case definitions.

## Overlap review

Open and closed PRs were checked at task start (68 open, 100 recently updated
closed), then searched specifically for V3 Sell and refreshed before publication.
Merged #1210/#1227 and prior #567, recovery notes and the attempt ledger were
reviewed. A concurrent #1283 merged during validation; the duplicate Rust patch
was removed and this packet was rebuilt around its actual parent/merge source.
No competing source edit remains. The bounded search snapshot and resolution
are retained in `pr-review.json`.
