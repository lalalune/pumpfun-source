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
