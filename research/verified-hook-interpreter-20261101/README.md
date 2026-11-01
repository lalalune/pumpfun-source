# Keep verified compiler hooks on the selected Python

Running `pump_build_verified.py` with an explicit Python interpreter does not
require a `python3` command on `PATH`. Its physical-source, root-rustc and linker
hooks nevertheless used `#!/usr/bin/env python3`. Cargo/rustc launch these hooks
directly, so an otherwise valid offline build failed in interpreter lookup.

Three small POSIX launchers now invoke the existing Python implementations using
the builder's `sys.executable`. The selected path and arguments are quoted. The
original three `.py` hook files, other compiler arguments, admitted linker inputs and
default linker script are unchanged. This applies the approach established by
[#2823](https://github.com/lalalune/pumpfun-source/pull/2823) to the separate
verified builder; that earlier correction covered `reconstruction/harness`.

The physical launcher's digest and selected interpreter path are included in the
build receipt and dependency-cache context. Text-order receipts also bind both
text launchers. Changing the route creates a different cache key and seed
admission refuses mismatching launcher/interpreter bindings. Old cache entries
remain intact. The interpreter path is recorded; this does not add a byte-level
binding for the Python executable or its standard library.

## Actual reproduction

This correction is tested on parent
`77548392322fb0ccda62081cbaac4f1da30b460d`, the UTF-8 log correction in
[#3923](https://github.com/lalalune/pumpfun-source/pull/3923).

```sh
python -B research/verified-hook-interpreter-20261101/probe.py \
  --repo . --sdk /absolute/platform-tools-v1.44 \
  --revision 77548392322fb0ccda62081cbaac4f1da30b460d \
  --expect base --output /new/base-proof
python -B research/verified-hook-interpreter-20261101/probe.py \
  --repo . --sdk /absolute/platform-tools-v1.44 \
  --expect fixed --output /new/fixed-proof
```

The probe stages exact production modules and compiles tiny generic fixtures
offline using the installed official v1.44 Cargo, rustc, linker and objcopy. It
does not run a produced artifact or VM. The selected Python is an isolated virtual environment at a path containing a
space. This preserves its identity on distributions that canonicalize loose
interpreter symlinks. An inherited incorrect `PUMP_VERIFIED_PYTHON` must be replaced. The
text-order control merely wraps the existing default `.text` wildcard; it does
not search compiler flags or layouts.

| Actual CLI cases | Parent | Corrected |
| --- | --- | --- |
| Ordinary build, Python available / absent on PATH | Success / lookup failure | Both succeed |
| Text-order build, Python available / absent on PATH | Success / lookup failure | Both succeed |
| Dependency-cache cold / warm, Python on PATH | Both succeed | Both succeed |
| Dependency-cache cold / warm / seed import, no Python on PATH | Three lookup failures | All succeed; warm/import are hits |
| Changed seed launcher / interpreter binding (corrected only) | Not applicable | Both refused before publication |

The nine common cases contain five original failures. All nine build successfully
after correction, and the two additional seed controls reject. The four passing
parent controls retain their artifact hashes. Ordinary and text-order builds
produce `7afbdfc8e467da02750384ee8f38a92dfbbc1876472ad19aa511a1a8c60837a1`;
all successful cached builds produce
`bc3fc52464f3398e02eef56e933ed71e6af1ee2ae5aab4f6bf07070b50ca1235`.
Source inputs, copied capture, installed tools, and existing immutable cache
entries remain unchanged. Owned Cargo bookkeeping and first-use crate extraction
are allowed and recorded separately.

The cache/seed fixture reuses the repository's unchanged official
[Inflector 0.11.4 archive and index](../../scripts/fixtures/cargo-index-case/README.md).
Unlike the original fixture's preparation-only test, this probe compiles the
crate with `default-features=false`. Its manifest has no build hook. The archive
and original 27 index records are checksum-verified, then wrapped in the same
explicitly derived Cargo v3 sparse-cache envelope. Actual Cargo generates the
lockfile and extracts the archive offline. Inflector is by Josh Teeter and
upstream contributors; its retained BSD-2-Clause notice applies. It is an
external compatibility fixture, not a claimed Pump dependency. No download is
performed.

## Regression and integration checks

`tests/test_verified_hook_interpreter.py` contains three always-on methods for
real launcher argument/interpreter transport, cache identities and seed guards.
Its fourth method repeats the eleven actual CLI cases when
`PUMP_BUILD_TEST_SDK=/absolute/platform-tools-v1.44` is set. All four passed
locally without skips; the normal contract-tests workflow discovers them.

The maintained UTF-8 log probe now includes the physical launcher when present
in its requested source revision. All thirteen real log workflows still pass,
with identical prior case outcomes and artifact hashes; raw log hashes vary
with temporary paths. Its historical README and results are untouched.

Required validation passed: 255 tooling tests and all nine capture checks.
Existing dependency-cache tests ran 15 methods with two optional SDK skips;
seven text-layout contract methods passed. Additional existing text-layout and
verified-tool-binding tests passed. Pending #3922's empty-digest guard composes
in either order with identical shared-module bytes and passing focused tests.

The actual compiler proof is macOS arm64 only. It establishes generic local
build-tool behavior, not a maintained Pump rebuild, new program behavior,
matching gain, runtime equivalence or Windows support. The mandatory unchanged
tooling suite separately includes its established runtime fixtures.
