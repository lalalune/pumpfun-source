# Preserve the V2 rent argument without changing dependency layout

**Current status: layout regression fixed.** Fresh control/candidate validation on
`381dc30b35122022be7359215cb5d471fe9f778d` retains **1,022 normalized / 276 raw**,
with zero gains and zero losses in either membership set. All four targets retain
ordered callee signatures versus control; the 416-byte helper remains normalized-exact.
Two candidate compilations produce identical complete unstripped and stripped ELFs.

## Source change and safety

Replace the unused `usize` rent-size argument with `#[repr(usize)] ZeroRentSize`,
a safe enum whose only variant is `Zero = 0`. Pass that variant at the three V2
call sites and use `size as usize` in `Rent::minimum_balance`. Every valid value
is zero, so the existing zero-data rent calculation is preserved by the type.
The cast keeps the argument live in the pinned compiler; it does not change the
helper's normalized machine body. There is no unsafe code, unchecked assumption,
exported symbol, duplicate matching helper, custom section, or compiler flag change.

The native-payments path crate and its Cargo changes are removed. Both helper and
transfer remain in their original modules, preserving the tail/dependency layout
and all 88 raw matches lost by the earlier cross-crate candidate. Source line
coordinates at existing code are retained. Only three production files differ
from the base: `buy_v2.rs`, `sell_v2.rs`, and `v2_native_payments.rs`.

| Target | Control bytes / ratio | Candidate bytes / ratio |
| --- | ---: | ---: |
| rent helper 0x3b598 | 416 / 1.000000 | 416 / 1.000000 |
| Buy V2 0x13b9b8 | 15488 / .953335 | 15512 / .973656 |
| Exact Quote V2 0x13f630 | 20192 / .978292 | 20216 / .993512 |
| Sell V2 0x144508 | 13944 / .951519 | 13968 / .962941 |

Buy V2 keeps its pre-existing original-callee mismatch; the other targets equal
original callee signatures. No new full-window match or VM/runtime qualification
is claimed. No backend stack warnings. Dependencies were reused, not rebuilt cold.
Root tooling passes 10 tests and all nine retained captures verify.

`current-main-comparison.json` and `current-main-builds.json` bind refreshed
memberships, source hashes, builds, toolchain checks and verifier. `verify.py` now
also requires strictly improved diagnostics for all three callers; comparing control
against itself correctly exits 1 (`rejected-unchanged-control.json`). The original
88-loss comparison remains in `rejected-cross-crate-current-main.json`.
`layout-fix-trials.json` records the bounded alternatives, including rejected
export/generic/runtime-assertion approaches and the unsafe-then-safe zero-type steps.

## Related PRs and merge coordination

- #1412 touches `buy_v2.rs` and `v2_native_payments.rs` and uses the same zero-size
  invariant through `unreachable_unchecked`, plus a separate whitelist binding change.
  This PR uses a safe zero-only enum and current-base checks instead. The whitelist
  work is not included. These are alternative rent implementations: retain one
  helper implementation when composing; do not stack the unsafe guard on this type.
  The invariant mechanism is overlapping prior work, not claimed as novel here.
- #1383 touches `v2_native_payments.rs` for the same residual using a black-box live
  helper and a matched twin. This PR keeps a single matching helper and verifies
  callers' actual callee signatures. The two helper implementations are alternatives.
- Merged #1356 supplies the layout whose 88 raw gains must be preserved; this fresh
  validation includes it and #1389 in base 381dc30. Earlier #1214/#1244 and the
  buyv2-sibling-transplant lane document the shared rent-argument residual.
- #1368 remains separate V3 sell work and is not included or revalidated here.

## Reproduce the current fix

Use the verified identity toolchain and the `fastbuild.py` commands below, replacing
historical base ef400863 with **381dc30** and using the current source for candidate.
Run the updated `verify.py` against the fresh unstripped outputs. Expect exit 0,
1,022/276 in both images, empty gain/loss lists, helper equality, preserved ordered
callees, and improved caller diagnostics. Rebuild the candidate to check both hashes.
Historical experiments below are retained for attribution and failed-path context;
their old no-loss/blocking claims do not describe the current implementation.

## Historical cross-crate attempt (superseded)

Base: `ef400863f4e476b2eaaab0866c0b1187d8060abc`.

The V2 rent helper already matches original window `0x3b598`, but LLVM sees its
unused `_size` argument in the same compilation unit and replaces the callers'
zero argument with poison. The original callers materialize zero in r2 and reuse
it for a None spill. Earlier buy/sell lanes documented this shared residual;
using `_size` inside `minimum_balance` improved callers but lost the helper match.

Move the existing V2 `ensure_rent_exempt` and legacy `transfer` definitions into a
local `pump-native-payments` crate, re-exporting both from their previous modules.
The V2 helper's call to transfer becomes local. All other function-body text is
unchanged. Moving transfer too avoids duplicating its implementation. There are
no new registry dependencies: the path crate uses the already locked anchor-lang.
The release profile, compiler, target libraries and scoring rules are unchanged.
This is a source-organization hypothesis, not authentication of the original crate
structure. Prior notes already identified a cross-crate solution in an older
snapshot; this contribution composes that mechanism on current main and verifies
that it preserves every current match.

## Measured results

| Original window | Original bytes | Control bytes / ratio | Candidate bytes / ratio |
| --- | ---: | ---: | ---: |
| `0x3b598` rent helper | 416 | 416 / 1.000000 | 416 / 1.000000 |
| `0x13b9b8` Buy V2 | 15,480 | 15,488 / 0.953335 | 15,512 / 0.973656 |
| `0x13f630` Buy Exact Quote V2 | 20,184 | 20,192 / 0.978292 | 20,216 / 0.993512 |
| `0x144508` Sell V2 | 13,976 | 13,944 / 0.939836 | 13,968 / 0.962941 |

The larger buy bodies are disclosed: ratio improvement is not exact equality or
a size improvement. The official scorer remains **1,020/1,035 normalized and
188 raw**, with zero gains and zero membership losses in either category.
All four targets preserve their control's ordered immediate-callee normalized-body
signatures. Helper, Exact Quote and Sell also equal the original's signatures.
Buy V2 retains its existing original-callee mismatch; it is not newly qualified.

`comparison.json` retains all matched-window memberships and bounded diagnostics.
`verify.py` recomputes them using the unchanged official scorer and rejects any
membership loss, loss of the helper match, or changed target callee signatures.
It decodes 16-byte lddw instructions without treating continuation slots as calls.
`source-sha256.json` binds all candidate crate inputs. `builds.json` records local
build hashes and backend stack-warning results. Build logs and ELF outputs remain
local; the commands below regenerate the evidence.

## Reproduce

Use the pinned identity toolchain documented in `reconstruction/README.md`.
The local SDK passed all 2,785 manifest entries and the hybrid check. Set the
objdump path to that verified SDK's `llvm/bin/llvm-objdump`. The local execution
used relocated SDK/cache paths; no compiler flags or compiler/library bytes changed.

From the repository root, choose fresh output/work directories:

```sh
git archive ef400863f4e476b2eaaab0866c0b1187d8060abc programs/pump | tar -x -C "$CONTROL_SOURCE"
python3.12 reconstruction/harness/fastbuild.py --src "$CONTROL_SOURCE/programs/pump" --work "$CONTROL_WORK" --out "$CONTROL_OUT" --recipe identity
python3.12 reconstruction/harness/fastbuild.py --src programs/pump --work "$CANDIDATE_WORK" --out "$CANDIDATE_OUT" --recipe identity
python3.12 reconstruction/pump-main/lanes/rent-argument/verify.py --control "$CONTROL_OUT/unstripped.so" --candidate "$CANDIDATE_OUT/unstripped.so" --objdump "$OBJDUMP" --output /tmp/rent-comparison.json
python3.12 -B scripts/test_tooling.py
python3.12 -B scripts/verify_evidence.py
```

Local checks: two candidate main-crate compilations produce the identical complete
unstripped ELF `2ac69c6942dc68b1e96067977ad9d553a2f289bbdf6c1e5c8dd1c1cbc5063cfe`
and stripped ELF `5258bfc36690165effbb4bbf97c1d68683b1c20cb45fa98211dac1f569614e5b`.
The standard control is unstripped `2364778f6dbd89927a406eed95451a72890c19331e9f9252b6837d9223a837de`.
An earlier control also emitted diagnostic LLVM IR; it has a different unstripped
symbol table but identical stripped hash `1589b4b61543c6f2a416f2e6458deabbd1f70fdb932bfd117ba509bed332ad2d`.
The published comparison uses the standard control. All builds have no backend
stack warnings. The 10 existing tooling tests and 9 captured-binary checks pass.
Builds reuse compiled dependencies; no cold dependency rebuild is claimed.

## Rejected experiment and limits

Making the unused `_size` parameter generic internalized/argument-promoted the
helper, losing six of its normalized slots and lowering the score to 1,019/188.
That experiment is excluded from the source change. Live ledger attempt ids:
`ace404f79ec847fd94d28cfd523cbb9a` (rejected generic) and
`170cec33ccad468b8c51d8f1b287cdb9` (cross-crate partial progress).

There is no new complete original-window match, whole-ELF equality, runtime/VM
execution, or security acceptance. Static call signatures do not establish runtime
equivalence. Full legacy CI was not run because it references removed packages.
Further source recovery remains necessary for all three handlers.

## Current-main regression and refreshed verification

The complete current-main control and merged candidate were freshly compiled using
verified macOS v1.44 identity tooling (2,785 SDK inventory entries and hybrid checks
pass). Both builds have no backend stack warnings. Dependencies were reused.
`current-main-comparison.json` retains full memberships and callee diagnostics;
`current-main-builds.json` binds source and build hashes. The verifier now follows
Sell V2's upstream outlined symbol, `pump_recovered::pump_recovered::sell_v2`.
It exits **1**, correctly rejecting the 88 raw losses; no scoring rules were changed.

The 416-byte rent helper still matches. All four targets preserve ordered callee
signatures versus control. Buy V2 retains its pre-existing original-callee mismatch.
Diagnostic ratios improve (Buy V2 .953335 → .973656; Exact Quote .978292 → .993512;
Sell V2 .951519 → .962941), but these improvements do not justify losing raw matches.

The new 1,616-byte native-payments object is linked between pump-token-ext and later
dependencies. This changes relative calls across that boundary. For example original
window 0x17c3d8 (Fee::calculate_fee) is raw-equal in control and normalized-only in
candidate, with changed call immediates at offsets 0x80 and 0x140. The loss set is
exactly the 88 raw gains delivered by upstream's layout change.

Rejected bounded alternative: start from current main without the new crate and add
`#[no_mangle]` to the existing `ensure_rent_exempt` definition, preserving source line
numbers. It retains 1,022/276 and an exported 416-byte helper, but callers' callee
signatures change and their diagnostic ratios worsen. It is not included in source.
`rejected-local-export-comparison.json` retains the failed check. No no-loss solution
is established; keep this PR draft pending a source-level layout-compatible approach.

Reproduce the current check using the prior build commands with base `6654999`, then
run the updated `verify.py` with fresh control/candidate outputs. Expect failure until
the raw membership regression is resolved. No VM qualification is claimed for this PR.

### Latest upstream follow-up

Create V2 change #1389 landed during validation. Merged `381dc30b35122022be7359215cb5d471fe9f778d`
and freshly rebuilt control and candidate again: identical membership verdict,
1,022/276 → 1,022/188, the same 88 raw losses, helper and ordered callee checks
preserved. Current-main JSON files now refer to this latest base; the rejected
local-export experiment remains explicitly tied to the prior 6654999 base.
