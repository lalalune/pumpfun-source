# Current main 094a06f validation (2026-10-29)

Fresh control and PR source 0ff8799 builds pass the unchanged verifier. Both 64-byte copy regions remain raw-equal to original: `0x13db90..0x13dbd0` and `0x142738..0x142778`. Exactly 16 byte positions change in the entire 1,934,648-byte stripped binary, none outside those regions. Function sizes remain 15,512/20,216; ratios improve 0.976818→0.979979 and 0.993917→0.996350. Both full functions remain unmatched.

All 1,024 normalized and 277 raw memberships are unchanged, with 90/131 ordered callees preserved against control. Buy's original-callee mismatch remains pre-existing; Exact Quote equals original. No stack warnings. `main094-comparison.json` and `main094-builds.json` retain memberships, hashes, source/build bindings and exact byte-scope measurements. No VM replay or whole-original identity is claimed. Related #1384/#1383 source alternatives remain uncomposed here; merged #1412 is included through current main.

## Earlier evidence (historical baselines)

## Current-main revalidation after merged #1412 (2026-10-29)

Merged main `04be15f61e66d27282e2af3d581de984389eac90` into this PR; tested source `0aca09c8924366f3c461152b862a85cb5d466f4c`. The merge preserves #1412's whitelist binding, live rent argument and inlined completion-helper changes. No further implementation change was needed.

Fresh identity control/candidate builds, using the same pinned toolchain and warmed dependencies, confirm:

| Target | Bytes, unchanged vs current control | Before ratio | After ratio | Exact original region |
| --- | ---: | ---: | ---: | --- |
| Buy V2 | 15,512 | 0.976818 | 0.979979 | `0x13db90..0x13dbd0` |
| Buy Exact Quote V2 | 20,216 | 0.993917 | 0.996350 | `0x142738..0x142778` |

Both 64-byte sequences remain raw-byte equal to the original, including registers and stack offsets. The candidate offsets within each function are `0x21d8` and `0x3108`. All 90/131 ordered immediate-callee signatures equal current control. Buy V2 retains its pre-existing original-callee mismatch; Exact Quote's signatures equal original. Both complete handlers remain unmatched.

Official memberships are **1,023 normalized / 276 raw in both builds**, with zero gains or losses. The entire stripped ELF is now **1,934,512 bytes** (the historical baseline below was 1,934,080): exactly **16 byte positions** change, eight per region, and **zero bytes outside those regions** change. Current stripped file ranges are `0x18d90..0x18dd0` and `0x1dd68..0x1dda8`. The larger ELF/handler sizes belong to upstream changes, not this patch.

- Control unstripped: `e4e090c5ac425e4e93e51bc5794b04fbcae1bc20fba7d76eb157f4428b30987e`.
- Candidate unstripped: `958b47649aec69eb37e0e2e6f51decf9474f51e651de6679426635e4378a60ee`.
- Control stripped: `7eee248f17559a76a15daa2897c33ab6d07e46b4a69479512bb41267ff5a73ba`.
- Candidate stripped: `262dd68e9dd9bd5b75e6014b8fa857b1d18312e3bc52b23fc544b62129666382`.

`current-main-comparison.json` retains complete memberships, copy regions and callee digests. `current-main-builds.json` binds both source trees, verifier and binaries. The unchanged `verify.py` passes; fresh negative controls reject both an unchanged candidate and an extra rodata-byte mutation (`current-main-negative-controls.json`). Both builds have no stack warnings. Ten root tooling tests and all nine saved capture checks pass; diff checks pass. These are two fresh main-crate compilations, not a cold dependency rebuild or VM replay.

Reproduce using the commands below, substituting main `04be15f61e66d27282e2af3d581de984389eac90` for the historical control revision and this tested source revision for the candidate. Keep the stripped `candidate.so` beside each `unstripped.so`. The verifier acceptance checks have not been relaxed.

Related PRs: merged [#1412](https://github.com/lalalune/pumpfun-source/pull/1412) changes the same handlers and is included in this measured control/composition. [#1384](https://github.com/lalalune/pumpfun-source/pull/1384) offers a safe zero-only replacement for its rent invariant and touches the same `buy_v2.rs`; that separate combined source build is not tested here. [#1383](https://github.com/lalalune/pumpfun-source/pull/1383)'s competing dual helper is not included. [#1368](https://github.com/lalalune/pumpfun-source/pull/1368) is historical V3 evidence, not part of this patch's gains. No new full-window match, whole-original ELF identity, runtime equivalence or security qualification is claimed.

## Historical pre-#1412 evidence

# Recover the shared V2 quote-mint snapshot copy

Base: `665499915f9caedcd38921d415a90f0606686398` (1,022 normalized / 276 raw).
Targets: Buy V2 `0x13b9b8` and Buy Exact Quote V2 `0x13f630`.

Both original handlers copy the quote-mint snapshot using four ascending,
interleaved 64-bit loads/stores. The reconstructed by-value Pubkey assignment
becomes one LLVM memcpy and emits descending copies. This residual was documented
by the earlier `buyv2-sibling-transplant` lane; its attribution is retained here.

Use an inlined helper to copy four constant, disjoint eight-byte slices directly
into the final Pubkey destination. These cover exactly the 32 source bytes and
preserve the value. No unsafe operation, bytecode injection, compiler modification,
black_box, duplicate matched function or runtime branch is added. This is a
source-level reconstruction hypothesis, not proof of historical source spelling.
Existing handler line numbers are preserved; the helper is appended at EOF.

Returning a new Pubkey from this helper instead made all four loads precede the
stores. Passing the destination by mutable reference avoids that temporary and
recovers the complete original sequence in each handler. See `experiments.json`
for the rejected and intermediate builds. Loop-based copies added calls and lost
62 raw memberships, so they were rejected. Whole-slice copy was byte-identical to
control. All retained trials built without backend stack warnings.

## Result

| Target | Bytes, unchanged | Before ratio | After ratio | Recovered original region |
| --- | ---: | ---: | ---: | --- |
| Buy V2 | 15,488 (original 15,480) | 0.953335 | 0.956499 | `0x13db90..0x13dbd0` |
| Buy Exact Quote V2 | 20,192 (original 20,184) | 0.978292 | 0.980726 | `0x142738..0x142778` |

Each recovered 64-byte region (eight instructions) is **raw-byte equal** to the
original, including its stack offsets and registers. At fixed positions all eight
slots previously differed. No other normalized bytes in either handler change.
The whole stripped ELF remains 1,934,080 bytes: **only 16 byte positions change**,
eight in each region. Every byte outside those regions is identical to control.

Full official membership: **1,022/1,035 normalized, 276 raw, no gains or losses**.
These are recovered regions within still-unmatched functions, not two additional
matched functions. Both retain their exact control ordered immediate-callee
normalized-body signatures (90 / 131 calls). Buy V2's pre-existing original-callee
mismatch remains; Exact Quote's signatures match the original.

`comparison.json` retains full memberships, region hashes and file offsets, call
signature digests and stripped-output comparisons. `verify.py` recomputes these
from fresh build outputs using the unmodified official scoring functions. It
requires the two exact original regions, unchanged sizes and call signatures,
no membership losses, and no stripped changes outside those regions. Negative
controls reject an unchanged candidate and a temporary extra rodata-byte mutation.

## Reproduce

Use the pinned identity toolchain described in `reconstruction/README.md`.
Create fresh control source, work and output directories; set `$OBJDUMP` to the
verified SDK's `llvm/bin/llvm-objdump`:

```sh
git archive 665499915f9caedcd38921d415a90f0606686398 programs/pump | tar -x -C "$CONTROL_SOURCE"
python3.12 reconstruction/harness/fastbuild.py --src "$CONTROL_SOURCE/programs/pump" --work "$CONTROL_WORK" --out "$CONTROL_OUT" --recipe identity
python3.12 reconstruction/harness/fastbuild.py --src programs/pump --work "$CANDIDATE_WORK" --out "$CANDIDATE_OUT" --recipe identity
python3.12 reconstruction/pump-main/lanes/quote-copy/verify.py --control "$CONTROL_OUT/unstripped.so" --candidate "$CANDIDATE_OUT/unstripped.so" --objdump "$OBJDUMP" --output /tmp/quote-copy-comparison.json
python3.12 -B scripts/test_tooling.py
python3.12 -B scripts/verify_evidence.py
```

Keep `candidate.so` beside each `unstripped.so`, as fastbuild does. The verifier
also checks those ordinarily stripped outputs. Local execution used relocated
SDK/cache paths, the existing identity compiler and target libraries, and warmed
dependencies. No cold dependency rebuild is claimed.

Two final main-crate compilations reproduce identical complete outputs:

- Unstripped: `b1f03fdb419afda4159f0b4217a2ad4e20a70bb0fdac6444ce37d0d7a5911c1b`.
- Stripped: `40496532e241852ebb4e77460ad4067bae58c0cf15a75e94c87892e6b59734a7`.
- Standard control stripped: `e412a3cbebea18b305e2915a79b5c8ef23606565dd8a3e24bac1a6bcc4cad66c`.

The comparison uses a standard control build. Some exploratory builds emitted
LLVM IR for diagnosis; only ordinary Rust compilation produced proposed outputs.
`source-sha256.json` binds the final crate inputs. ELF/build-log outputs remain
local and can be regenerated; no personal machine paths are retained here.
The 10 tooling tests and 9 capture-integrity checks pass. The final hypothesis is
recorded in the shared ledger as `5b59c5fb0fbf45249629548a7852f085`.

This change is independent of the rent-helper proposals #1383/#1384 and V3 Sell
#1368. No VM execution, full-function match, whole-original ELF identity or runtime
security qualification is claimed. Full legacy CI references removed packages and
was not run. Further source recovery is needed for both handlers.
