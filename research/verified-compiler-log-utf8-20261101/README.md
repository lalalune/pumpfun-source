# Preserve verified-build results across Python locales

The verified builder writes compiler output directly to `build.log`, then reads
that file to check stack diagnostics. `DependencyCache.finish` reads the same log
again to account for Cargo artifacts. Both readers used the host locale.

On base `60a42309a4908577f0a386513eeaee6cd6f84f42`, a real UTF-8 warning under
an uncoerced ASCII Python locale makes a successful compilation raise
`UnicodeDecodeError` before publication. A real compilation error similarly
leaves `build-attempt.json` without the compiler return code or log hash. The raw
log already exists; this is lost result processing, not lost compiler output.

Both readers now explicitly decode UTF-8, retaining strict decoding. Compiler
status, stack filtering, raw log bytes, cache membership and publication rules
are unchanged. This follows the locale-independent harness correction in
[#2448](https://github.com/lalalune/pumpfun-source/pull/2448) and preserves the
UTF-8 evidence writers from [#3096](https://github.com/lalalune/pumpfun-source/pull/3096).
Those changes did not cover these two readers.

## Reproduction

```sh
python -B research/verified-compiler-log-utf8-20261101/probe.py \
  --repo . --sdk /absolute/platform-tools-v1.44 \
  --revision 60a42309a4908577f0a386513eeaee6cd6f84f42 --expect base --output /new/base-proof
python -B research/verified-compiler-log-utf8-20261101/probe.py \
  --repo . --sdk /absolute/platform-tools-v1.44 --expect fixed --output /new/fixed-proof
```

The probe copies exact production modules into a temporary cohort and authors
small generic `no_std` crates. It runs actual offline v1.44 Cargo, rustc, linker,
physical source wrapper and objcopy. The cache fixture is an owned Cargo directory
source, not a claimed published registry package. No compiler, emitted artifact,
cache result or compiler log is mocked. The output directory retains raw logs,
stderr and the structured result. The temporary source/build trees are removed.

There are thirteen actual builds per revision:

| Cases | Base | Fixed |
| --- | --- | --- |
| Unicode warning, ASCII locale | Decode error after successful compile | Successful comparison; same ELF as UTF-8 control |
| Unicode compile error, ASCII locale | Decode error; no compiler code in attempt | Cargo status 101 retained; no successful comparison |
| Unicode cache hit and fresh cache, ASCII locale | Decode errors | Hit/miss both succeed with the seed ELF hash |
| Unicode direct-cache compile error, ASCII locale | Decode error | Direct rustc status 1 retained; no successful comparison |
| Four ASCII diagnostic cases and four UTF-8 controls | Correct statuses | Unchanged statuses and artifacts |

Five locale-induced failures become zero. All actually compiled ELF hashes are
unchanged across revisions; successful direct outputs hash to
`eef26ed23477fc5d99af35da1f74c0977eeabc1ebe95fc237616a83a625b0a0d`, and cache outputs to
`730f6b96c2744689dce26428a0fd17895b8d37f8f14cf0b9f87261404ba3c3c9`.
Source/dependency inputs, existing immutable cache entries, copied capture and
compiler tools remain unchanged. The cargo/rustc/objcopy hashes match the
repository's `reconstruction/toolchain/v1.44-macos-inventory.json`.

## Validation and limits

`scripts/test_verified_compiler_log_encoding.py` has three always-on methods
covering real CLI receipt publication with the existing explicitly synthetic SDK
transport, cache publication, and strict rejection of malformed UTF-8. They are
CI regressions, not the compiler proof above. Its fourth method repeats all
thirteen real builds when `PUMP_BUILD_TEST_SDK` points to the installed v1.44 SDK.
All four passed locally without skips. Eighteen existing affected methods,
255 required tooling tests, and all nine capture checks passed.

The public proof compiles generic diagnostic fixtures and performs static byte
comparison only; it executes no produced program or VM. The unchanged mandatory
tooling suite separately includes its existing runtime fixtures. This does not
claim a maintained Pump rebuild, additional reconstructed behavior, matching gain,
arbitrary non-UTF-8 diagnostic support, or locale independence of every manifest
and metadata reader. No prior package, capture, program source or compiler option
is changed.
