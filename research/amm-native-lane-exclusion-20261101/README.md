# Native AMM lane exclusion

Two native builds with different IDs can use the same lane. Cargo's target lock
starts after workspace staging: a second invocation can replace `sell.rs` while
the first compiler is waiting in a build script. On base `9120883a957d7d9b2cab6140f66fb5bc9e6774d5`,
the first successful record names source A's SHA-256 but its real SBF ELF equals
the serial source-B build. That makes the recorded experiment unreliable.

Hold a nonblocking POSIX advisory lock on the lane from before `ensure_lane`
through artifact publication. A competing native builder receives an error before
staging. Distinct lanes remain independent. The lock file stays in place so all
participants keep using one inode; closing it releases the lock, including after
an exception. This coordinates cooperating native-build invocations on supported
local POSIX filesystems, not arbitrary file writers or distributed filesystems.

## Reproduce

```sh
python -B research/amm-native-lane-exclusion-20261101/probe.py <repository> <v1.44-macos-sdk>
PUMP_BUILD_TEST_SDK=<v1.44-macos-sdk> python -B tests/test_amm_native_lane_lock.py
```

`probe.py` runs the actual `native_build.build` workflow, including rsync, Cargo,
the production compiler/linker wrappers, rust-lld, and objcopy. It authors a tiny
no-std two-package SBF fixture, records that fixture's real compiler metadata, and
pauses source A in a genuine Cargo build script. While A waits, it starts source B
in the same lane and also completes B in a different lane. It then releases A and
compares the output with serial A/B controls. Both revisions use this same probe.
The metadata map is specific to this fixture; its Linux/macOS metadata are equal
by construction, without claiming to reproduce a historical Linux recipe.

The authenticated official v1.44 SDK and archive SHA-256 are recorded in
`results.json`. It is used in place without changing the SDK or installing to a
user-global location. The probe keeps Cargo state and artifacts in a temporary
directory, runs offline, and removes its temporary tree on completion.

Before: both same-lane calls succeed, the staged source changes under A, and A's
ELF equals B's control. After: A succeeds with its own control ELF, B is rejected
before staging, and the different-lane build still succeeds while A is paused.
Source A's recorded SHA-256 remains the actual selected source hash in both runs.
`results.json` retains the exact hashes and process outcomes.

Validation: 4 new tests passed with the real SDK, including separate-process
same-lane rejection, distinct-lane acquisition, and release after a real setup
failure; 9 existing lane tests, 3 native preservation tests, 250 tooling tests and
9 captured-evidence checks passed. CI runs the 3 portable POSIX process tests;
the genuine macOS SBF probe runs when `PUMP_BUILD_TEST_SDK` is provided.

Limits: this proves native build coordination with a tiny real SBF fixture, not
a rebuild of the maintained AMM program, a matching gain, or whole-program ELF
identity. No reconstruction source, original capture, compiler recipe, or scoring
rule changes.
