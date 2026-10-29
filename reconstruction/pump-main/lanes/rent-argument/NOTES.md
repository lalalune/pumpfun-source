# Preserve the V2 rent helper's zero argument across the crate boundary

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
