# macOS bootstrap publication interruption

At base `ed47ac72a632e54a4d5ca9a192912c8d5b40faf2`, macOS bootstrap asks the shell assembler to replace the canonical toolchain directly. The assembler first moves the old tree aside, leaving the canonical path absent until a second move. A killed bootstrap during that interval leaves an existing runnable compiler unavailable. Linux bootstrap already uses locked atomic publication.

`probe.py` runs the actual bootstrap against the official v1.44 macOS SDK, using fresh temporary cache paths. It first assembles a runnable toolchain, adds an unused old dylib to request replacement, and interrupts the replacement immediately after its actual canonical-path rename. The observation adapters execute the real rename before signaling the watchdog; no compiler or filesystem result is fabricated.

The same probe on the base records `canonical_exists_after_interrupt: false` and `canonical_compiler_runnable_after_interrupt: false`. With this change both are `true`, and the previous installation's marker remains available in the exchanged staging tree. `before.json` and `after.json` retain the exact output. The macOS path now uses the existing publication lock and native exchange/no-replace primitive, verifies a private staged tree, and preserves the old tree as a backup. Cleanup checks inode ownership so an interrupt immediately after exchange cannot delete the previous installation.

SDK provenance: [official v1.44 macOS archive](https://github.com/anza-xyz/platform-tools/releases/download/v1.44/platform-tools-osx-aarch64.tar.bz2), SHA256 `66e20d135fddd70ff519baf7ff320d762957f9aedf93a50e23756db23ad79351`, 400794156 bytes. Full verification against the repository's 2785-entry SDK inventory passed. The SDK was extracted into an isolated task directory, with no global installation or home-cache changes.

Reproduce on macOS with an authenticated extracted SDK:

```sh
python -B research/macos-bootstrap-publication-20261031/probe.py "$PWD" /path/to/platform-tools
PUMP_BUILD_TEST_SDK=/path/to/platform-tools python -B reconstruction/toolchain/test_bootstrap_macos_publication.py
```

The five local tests passed, including the genuine pinned-compiler interruption probe. Four lightweight filesystem tests cover actual replacement, interruption, competing assemblers, and a late destination; those use a fixture compiler that only prints its sysroot and run in macOS CI. The full toolchain suite passed 39 tests with the SDK-dependent test explicitly skipped when its environment variable is absent; 17 Linux publication tests, 250 tooling tests, and all nine evidence captures also passed.

This proves bootstrap publication availability and retained recovery data. It does not claim an SBF rebuild or byte equality. The standalone shell helper is unchanged; bootstrap now invokes it only for a fresh private staging path.
