# Preserve executable inputs in the supported SBF adapter

The supported adapter admits a Rust build script and explicitly selected helper
assets, then stages every input using `copyfile`. That preserves bytes but drops
execute permission. A source crate whose `build.rs` invokes its selected `.sh`
helper builds directly, while the adapter's copied crate fails with PermissionDenied
and `source_unchanged=true`.

Use `copy2` for source staging so the selected file modes are preserved. A helper
that was not executable remains nonexecutable; the adapter does not grant execute
permission to arbitrary source files. Other artifact-copy paths are unchanged.

## Full supported workflow proof

```sh
python -B research/supported-build-executable-inputs-20261101/probe.py <repository> <tool-root>
PUMP_TEST_RUST_BIN=<host-rust-bin> PUMP_SUPPORTED_TEST_TOOLS=<tool-root> python -B tests/test_supported_executable_inputs.py
```

`<tool-root>` contains `v1.53/platform-tools` and the pinned
`v1.52/platform-tools/llvm/bin/llvm-objcopy`. The official release asset digests,
archive sizes and selected tool checks are in `results.json`. Both downloaded
assets matched publisher SHA-256 values; all 38 v1.53 files and 3 extra tools match
the unchanged production policy, as does v1.52 objcopy. No installer or SDK source
workspace is run. The compiler uses its prebuilt sysroot, and compilation is offline.

The same probe runs the production `plan` and `execute` APIs with their unchanged
v1.53 policy; the existing `cache_root` parameter locates the isolated toolchain.
It authors a tiny no-std source crate whose real Rust build script invokes an
explicitly admitted shell source helper. There are no compiler, filesystem, plan,
result or artifact mocks. Each source also receives an independent direct Cargo
build with the same compiler flags and stripper. Temporary inputs, Cargo state and
outputs are removed; the installed SDK is read only.

On base `9120883a957d7d9b2cab6140f66fb5bc9e6774d5`, an executable source helper changes
from 0755 to 0644 during staging. Direct compilation succeeds, while the adapter
returns 101 at `compile_failed` with PermissionDenied. After the fix, it retains
0755 and the complete adapter build emits the same stripped ELF as the direct
control: `56f01efa524d98da3f53429194857dfe6c0c19641dec7fa9940461bb308d80fa`.
The 0644 negative control still fails both direct and staged compilation. Exact
statuses, modes and hashes are retained in `results.json`.

`staging_probe.py` separately extracts the actual production staging loop by AST
and runs a real offline host Cargo build: before, original output is 37 and staged
compilation fails; after, both output 37. This bounded loop test runs in CI when
Cargo/rustc are available. The complete macOS SBF probe requires the SDK variable
above. CI's existing contract-tests job discovers both test methods.

Validation: both new actual-compiler tests passed; 250 tooling tests and all 9
captures passed. Broader `scripts/test_supported*.py` discovery runs 32 tests:
23 pass and the same 9 tests error on the base and fix because historical
`repro/build-tooling/supported-sbpf-integration` and `supported-sbpf-proposal`
fixtures are absent from current main. That historical suite is not reported as
passing; the current adapter path/stack/source-binding controls pass.

Limits: tiny source fixture and compiler workflow only, not a maintained Mayhem
rebuild, historical identity, matching gain or runtime equivalence. Program source,
captured artifacts and measured policy hashes are unchanged. This preserves copied
source modes; it does not extend the existing source receipt into a hermetic metadata
or concurrent-file-mutation guarantee.
