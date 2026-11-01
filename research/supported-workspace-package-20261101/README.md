# Select the requested supported-build package

The supported v1.53/v1.54 adapter derives its library output from the supplied
`--manifest`, but previously passed only `--manifest-path` to Cargo. For a package
manifest at a workspace root, Cargo instead selects `workspace.default-members`
when present. Those members can exclude the requested package. The actual
compiler then succeeds, while the adapter fails to find the requested library.
This is documented [Cargo package-selection behavior](https://doc.rust-lang.org/cargo/commands/cargo-build.html#package-selection).

The command now also passes `--package` with that manifest's package name as one
argv element. The package name and explicit library name can differ. Source
staging, manifests, lockfile, profiles, target, linker/strip tools and output
admission are unchanged; the recorded command exposes the selection. This does
not change the frozen historical helper or its provenance rules.

## Actual offline reproduction

```sh
python -B research/supported-workspace-package-20261101/probe.py \
  --repo . --tools /absolute/owned-solana-cache \
  --revision 60a42309a4908577f0a386513eeaee6cd6f84f42 \
  --expect base --output /new/base-proof
python -B research/supported-workspace-package-20261101/probe.py \
  --repo . --tools /absolute/owned-solana-cache \
  --expect fixed --output /new/fixed-proof
```

The tool root contains the already-installed official v1.53 platform-tools and
the policy's pinned v1.52 objcopy. The probe copies exact production sources into
an owned cohort, then invokes the real adapter's argument parser and `plan` /
`execute` API with its explicit `cache_root` parameter. No production function,
tool hash, policy, compiler result or output artifact is substituted. This is
not an end-to-end CLI default-home discovery claim.

There are seven generic source cases per revision, each also compiled by an
independent direct Cargo command that explicitly selects the package:

| Source configuration | Base adapter | Fixed adapter |
| --- | --- | --- |
| Standalone workspace package | Success | Success |
| Root package, implicit default | Success | Success |
| Root package, explicit root default | Success | Success |
| Root package, sibling-only default | Missing requested library after compiler exit 0 | Success |
| Root package, root and sibling defaults | Success | Success |
| Explicit member manifest | Success | Success |
| Root package with path dependency, sibling-only default | Missing requested library after compiler exit 0 | Success |

Both failures become successful builds of the requested root package. All seven
corrected artifacts match their direct explicit-package controls, and the five
passing base outputs keep identical hashes. Root artifacts hash to
`56f01efa524d98da3f53429194857dfe6c0c19641dec7fa9940461bb308d80fa`;
the selected sibling artifact hashes to
`ab61aeda3963e829535637fa9b2514c3894cb319fb57c3e25eda55368413df87`.
The local path dependency still compiles. Hyphenated package names differing
from library names are selected literally.

All caller sources, effective copied manifests/lockfiles, copied capture and
recorded Cargo/rustc/objcopy files are preserved. The source fixtures have no build scripts or
registry dependencies. The owned offline registry stays empty; normal Cargo
bookkeeping creation is recorded separately and existing cache bytes stay
unchanged. Raw adapter logs and direct-control stderr are retained in the
requested proof directory. No emitted image, model or VM is executed.

## Validation and bounds

Three new methods pass with `PUMP_SUPPORTED_TEST_TOOLS` configured, including all
seven real adapter workflows and seven direct compiler controls. Without an SDK,
two planning regressions run with explicitly synthetic nonexecuting policy
fixtures and the real-compiler method skips. Existing contract-test discovery
includes the new file. Twenty existing entry-path, stack-admission, routing and
source-inventory methods pass. Required validation also passed: 255 tooling tests
and all nine capture checks. Four existing historical package-path controls pass.

The existing archived proposal/integration fixtures are absent from current main;
this change does not manufacture or repin their source bindings. The immutable
source-inventory utility and supported SDK policies stay byte-identical.

The actual proof uses macOS arm64 and the existing measured v1.53 recipe. It does
not establish a maintained Pump rebuild, byte-match gain, runtime equivalence,
other-host support, or a new compiler recipe. The unchanged mandatory tooling
suite separately includes its established runtime fixtures. Earlier
[#2328](https://github.com/lalalune/pumpfun-source/pull/2328) selected the correct
library filename in the separate fastbuild harness; this correction selects the
package that the supported adapter actually asks Cargo to build.
