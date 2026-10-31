# Exact-body inventory executable identity

`pump_exact_body_inventory.py` extracted symbols with `llvm-objdump`, then
reread that executable's path after comparing the function windows. An SDK
tool replacement in between bound the successful report to executable bytes
that had never produced its symbols. Deleting the path after extraction also
discarded an otherwise complete analysis with `FileNotFoundError`.

The fixed CLI reads one executable snapshot, uses that private file for symbol
extraction, checks that the private file stayed unchanged, and records the hash
of those admitted bytes. The usual LLVM `bin/../lib` lookup is preserved. The
hash identifies the executable, not its shared libraries.

## Actual retained-artifact reproduction

Base: `9120883a957d7d9b2cab6140f66fb5bc9e6774d5`.

The input is the unchanged decompressed
`reconstruction/pump-main/lanes/v3-sell-payment-layout/candidate.so.gz`, SHA-256
`969811b0e0f673b693695ea651008cacd93eafa5a663dd8bec0e61d3b22d09a9`.
The native macOS aarch64 tools are from official platform-tools v1.44:

- `llvm-objdump` 18.1.7: `24f83fd4c314fdc358920bf9936261985b8c39266f1ba7d556716c9dec1d24f9`.
- Replacement `llvm-readelf`: `5b68fb13a7ddef44a8bf2b4068496113c448ec5bac7507b05aab8590c78f06a5`.

The probe invokes the actual CLI using an owned tool copy. An observer waits
for the genuine `pump-symbols-*` temporary input to appear and disappear, then
atomically replaces the original tool path with the official `llvm-readelf`
binary. That input closes after `llvm-objdump` returns; the replacement is never
used for symbol extraction. Both replacements reproduce the wrong hash on base
and retain the executed `llvm-objdump` hash after the fix. A deletion control
fails on base and completes after the fix. The stable-tool control succeeds on
both revisions.

Every successful run has the same 1,035 window rows, 188 raw-equal windows and
canonical window-row SHA-256
`90492db28b9fb81525eb3b6a48c94731f0d982a3fdd456366fac6c2164d33748`.
`results.json` retains the four cases per revision. No input ELF is modified.

From the fixed checkout, supply the SDK directory and a fresh output path:

```sh
python -B research/exact-body-tool-identity-20261101/probe.py \
  --checkout "$PWD" --sdk /path/to/platform-tools-v1.44-osx-aarch64 \
  --candidate /path/to/decompressed-candidate.so \
  --output /path/to/fresh-results.json --expect fixed
```

Use this same probe against a clean base checkout with `--expect base` for the
before comparison. The probe fails if it misses the observed extraction window
or if the recorded hashes, counts or report contents differ from the retained
postconditions. Only owned temporary tool copies and outputs are changed.

## Regression and limits

`scripts/test_pump_exact_body_tool_snapshot.py` covers replacement, deletion,
private-snapshot mutation rejection, cleanup, and the LLVM library layout.
Those deterministic regression tests substitute symbol extraction; the actual
CLI evidence above uses the real SDK executable and retained symbol ELF.
The existing parsed-window snapshot regression remains in place.

This qualifies executable attribution on macOS. Native Windows, arbitrary tool
wrappers with additional relative-file dependencies, shared-library identity,
and hostile filesystem races are not qualified. There is no new source build,
program execution, reconstruction gain or runtime-equivalence claim.
