# Bind saved Relay IDL receipts to the complete producer plan

At upstream base `e87e001da16c4c7ce3d0a3ff0d6d5783ae1d99f7`, the independent
IDL verifier accepts a genuine 27-step receipt after it is reduced to two
transactions and its self-reported counts are updated. Both cases remain
nonempty, their classifications remain equal, and the retained transactions
are genuine, uniquely signed original/candidate comparisons. The report still
claims the complete lifecycle through its unchanged `operation_order` field.

The same gap admits omitted, reordered and duplicate logical step identities.
An exact ordered cohort check is needed; a minimum count alone cannot detect a
duplicate label or a contradictory declared order. The fixed producer has no
partial-case mode.

## Source and relationship to prior work

- `producer.py:286-344` produces the ordered eleven-step persistent lifecycle.
- `producer.py:347-421` produces the sixteen admission steps.
- `producer.py:473-535` always emits both cases and derives transaction totals
  from their contents. Its `inputs.upstream_commit` is a historical anchor;
  the actual tested Git revisions are recorded below and in each environment.
- The package README documents the complete lifecycle and verifier command.
- #2415 established the signed replay. #2520 checked case/control membership;
  #2717 rejected empty cases and explicitly left step-plan comparison outside
  its scope. This change retains both protections and checks the whole cohort
  in one change. The producer, build recipe and previous evidence are unchanged.

## Real before/after proof

Both runs use the same `reproduce.py` and `probe_real_reports.py`, Python 3.12,
solders 0.27.1, and the official native macOS arm64 v1.44 SDK. The caller checks
the official archive SHA256
`66e20d135fddd70ff519baf7ff320d762957f9aedf93a50e23756db23ad79351`
and runs `bootstrap.py --sdk-check full` before the proof. The proof fetches the
locked crates with the SDK Cargo and invokes the existing unmodified builder.
There are no patched SDK files, compiler substitutions or binary edits.

| Run | Actual tested commit | Result |
| --- | --- | --- |
| [Before 41145311264](https://github.com/miracle2044/pumpfun-source/actions/runs/41145311264) | `c25ecee6cb3f44405da39e715d08e4fa36573ead` | full control passes; eight invalid plans incorrectly pass |
| [After 41145386828](https://github.com/miracle2044/pumpfun-source/actions/runs/41145386828) | `a90d9e3849336e81444fc28727c75036d65bced0` | full control passes; all ten negative copies reject |

Each run freshly builds the candidate, executes the unchanged producer twice,
and compares the two complete reports byte for byte. Each report has eleven
lifecycle and sixteen admission steps, 27 unique verified signatures and 54
original/candidate VM sends. Signature and blockhash verification remain enabled;
there is no public RPC or privileged signer injection.

The candidate SHA256 is identical before and after:
`810df19bdae4af7540a844f8873bf09196cb5e42a867b77e3e007f3f1363dd92`.
SDK tool hashes, source manifests and all original/candidate case receipts are
identical. The complete positive reports differ only in `test_package_files`,
which correctly binds each current verifier version. The original reports have
not been rewritten to obtain this comparison.

The probe creates only labelled negative copies of that genuine control:
drop, reorder or repeat a logical label in each case; contradict the declared
lifecycle order; truncate both cases to one step each. It recomputes transaction
totals from the retained genuine signatures. All eight passed before and reject
after. A repeated real signature and an empty case reject on both revisions.
No positive fixture or VM receipt is synthesized by the probe.

Both hosted runs also pass the existing nine lifecycle tests,
`scripts/verify_evidence.py` and all 228 `scripts/test_tooling.py` tests. The two
existing `test_verify_steps.py` checks additionally pass locally with Python 3.11;
they use only the standard library. The supported hosted Python 3.12 runs are
the primary build/runtime proof.

## Reproduce and inspect

Use a fresh checkout at either full tested commit and the authenticated native
Mac SDK in `~/.cache/solana/v1.44/platform-tools`, with repository requirements
installed. Run:

```sh
python -B reconstruction/toolchain/bootstrap.py --sdk-check full
python -B research/relay-idl-plan-binding/reproduce.py
python -B scripts/verify_evidence.py
python -B scripts/test_tooling.py
```

The proof selects its expected before/after admission results using explicit
reviewed verifier SHA256 values, never by replacing the verifier. Output is
under `work/scoped-proof`; fresh build intermediates are outside that receipt
directory at `work/relay-plan-build`.

`receipts/{before,after}/` retains the genuine compressed producer report,
unmodified raw and stripped candidate ELFs, build and test logs, environment
and command-output verdicts. `receipt-files.json` hashes those retained files;
`comparison.json` records the cross-run checks. Negative report hashes and
actual CLI output are in `verifier-evidence.json`; their full JSON is reproducible
from the retained genuine control with the probe script.

This verifies complete saved-plan admission and a finite IDL differential. It
does not authenticate arbitrary external JSON, add contract behavior coverage,
prove whole-program or deployed-byte identity, reconstruct source, or establish
security acceptance. The ordinary native Mac build is not PR #2305's separately
qualified exact Linux layout. Historical packages and stopped lanes are untouched.
