# Ambient Cargo linker overrides in fastbuild

The documented fastbuild recipe isolates the staged release configuration from
ambient Cargo overrides. On base `d530a712c5d430399e06a70a3fcfd9106e54f6c9`,
`_build_locked` removes profile, incremental and workspace-wrapper overrides but
passes `CARGO_TARGET_<TRIPLE>_LINKER` to Cargo. A shell-exported linker can thus
replace the recipe's linker or cause its root linker hook to reject the incoming
arguments. Target settings can also select linkers for host build artifacts.

The fix removes every `CARGO_TARGET_*_LINKER` setting before the pinned
`link_order.configure` environment is applied. This follows the existing removal
policy for compiler/profile overrides, rather than adding ambient settings to a
recipe that is documented as fixed. Build-slot controls remain available.

## Same-method evidence

`before.json` and `after.json` contain real compiler results from
`reconstruction/harness/test_fastbuild_ambient_linkers.py --probe` on Linux
x86_64, with installed Cargo/rustc 1.95.0. `proof.json` binds their hashes to
the base and changed production source and to the unchanged regression script.
Only temporary path prefixes are replaced by `<proof-root>` in captured logs.

The probe uses the real `fastbuild.build` staging, environment construction,
source admission, process runner, compiler wrapper and offline Cargo build. It
selects the installed host toolchain and a dependency-free authored cdylib. It
observes the compiler's actual return value and then deliberately stops before
SBF-specific publication, since native libraries use a different output name.
Successful native outputs are hashed, loaded, and called through `ctypes`.
No compiler result or executable is mocked.

| Same fixture and source SHA-256 | Clean environment | Exported missing linker |
| --- | --- | --- |
| Base | Cargo exits 0, function returns 42 | Cargo exits 101: linker not found |
| Fixed | Cargo exits 0, function returns 42 | Cargo exits 0, function returns 42 |

All three successful outputs have SHA-256
`350d460afaead98f1529d34e47bf1ed20502a4cf456bb5451874d5df602a5808`.
All four source manifests have the same digest. The committed regression fails
on the base and passes with the fix, including exact native-output equality.
The existing controlled environment regression additionally checks removal of
both SBPF-target and native-host linker settings and retention of build jobs.
Both regressions run in the existing `fastbuild-staging` CI suite.

Validation on the changed tree: all nine retained captures verify; all 250
`scripts/test_tooling.py` tests pass. The native regression, existing ambient
override checks, staging, output-race, publication, library-name and linker-hook
suites total 32 passes and two explicit SDK-dependent skips.

Run on the fixed checkout:

```sh
python3 -B reconstruction/harness/test_fastbuild_ambient_linkers.py -v
python3 -B reconstruction/harness/test_fastbuild_ambient_linkers.py --probe
python3 -B reconstruction/harness/test_fastbuild_ambient_overrides.py -v
```

For a before/after replay, create a separate worktree at the recorded base,
copy only `test_fastbuild_ambient_linkers.py` into its harness directory, and run
the same commands there. The test exits 1 on the base; `--probe` emits its
observations without imposing the fixed behavior. No registry dependencies are
downloaded. The host probe requires GNU Linux, Cargo, rustc and rsync; it uses
`RUSTC_BOOTSTRAP=1` solely for the production recipe's existing
`-Zremap-cwd-prefix` flag.

Limits: this demonstrates compiler-environment isolation through actual native
compilation. It does not build a maintained SBF program, qualify the v1.44
toolchain, score a new bytecode match, or establish runtime equivalence or
security acceptance. No program source, captured ELF, historical package or
scoring rule changes.
