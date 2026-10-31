# Bind AMM attempt inputs to the bytes used by the builder

Base: `90300f9d2efe3ef014b116172251a41bfb104d78`.

The attempt runner hashes an optional linker script only when its contents are
nonempty. An explicit empty script therefore shares the default-script cache
key, although the native linker wrapper sends different scripts to LLD. The
runner also hashes external sell, patch and linker files before the builder
reopens their mutable original paths.

The fix retains the admitted bytes and passes those retained paths to the
builder. Explicit empty files receive the SHA-256 of empty bytes; absence remains
`null`. Snapshots are published by replacement after a complete temporary write,
so concurrent identical attempts cannot expose a partially rewritten snapshot.

## Real linker evidence

```sh
python research/amm-input-binding-20261031/probe.py /path/to/checkout /path/to/rust-lld /path/to/clang
```

The probe compiles one C function to an x86-64 ELF object, then runs the unchanged
native `LINKER_WRAPPER` with the repository's pinned default input script. It
exercises default linking, an explicit empty script, and a script changed after
admission. Before the helper exists, admission uses the unchanged statements
extracted from the base runner's AST; afterward it uses the production helper.
All linker results and ELF bytes come from real processes.

| Case | Base admission | Base linked ELF | Fixed result |
| --- | --- | --- | --- |
| Default | key `b665def3…` | 1,368 bytes, SHA `299776f2…` | default preserved |
| Empty override | same key `b665def3…` | 1,856 bytes, SHA `e9f62999…` | distinct key, empty hash retained |
| Edited after admission | ordered script hash `9c9ec5d1…` | empty-script ELF `e9f62999…` | admitted script used, ELF `299776f2…` |

`before.json` and `after.json` retain full keys, script hashes and ELF hashes.
Recorded tools: Apple Clang `21.0.0 (clang-2100.3.34.2)`, official Rust-distributed
LLD `23.1.1` at LLVM revision `1b9c0d5ff9bbe7634aead059efe6b11a7eeba145`,
CPython 3.12.13 on macOS arm64.

`tests/test_amm_input_binding.py` also executes the actual attempt runner,
rsync and patch while changing each original input immediately after admission.
An intentionally absent SDK stops those staging tests at the compiler boundary;
no successful compiler result is fabricated. Both sell and patch attempts stage
their admitted bytes and retain the admitted link script. The real linker probe
runs when Clang and LLD are available (`PUMP_TEST_CLANG` and `PUMP_TEST_LLD` can
select explicit tools), and the test is invoked by the verification workflow.

This is a tooling identity/linking reproduction using a host ELF fixture. It is
not an SBF reconstruction build, score improvement or runtime acceptance claim.
Maintained program source and historical captures remain unchanged.
