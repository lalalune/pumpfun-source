# Complete target-directory exclusion boundary

The original nine-case packet in the parent directory is unchanged. Independent
review then used one actual rsync staging call to confirm a related inherited
edge: `/target/` excludes a real root directory but preserves a root directory
symlink named target. Both the base and initial proposal omitted that link
before reaching the existing directory-symlink rejection. The reviewer kept
that source-staging proof privately; no compiler or security impact was claimed.

Validate source directory links before pruning the real crate-root target
build directory. Keep Git metadata exclusion, the existing rsync arguments,
compiler flags and every other file check unchanged. A root module referring
to `../target/mod.rs` through the source symlink is now rejected.

The corrected method adds one root-link control to the earlier nine tests:
seven original controls plus three regressions, ten unique tests total.
Repeated controls are not additional unique cases.

The exact same method, with production modules authenticated from base
`6a1d23a306ce0b2213aac937d7a81472efe5986b`, first gives three failures.
After source commit `c8ecaf1005de193032950780c2f778786d296e0f`, it gives
ten passes. Both runs used the same isolated path containing spaces, real
rsync, and exact method bytes from commit
`f6629790e26056a377098c046d808d799ffa2965`. The JSON records bind all four
Python inputs and preserve the original failure output.

Normal replay with rsync installed:

```sh
python3 -B reconstruction/harness/test_source_inputs.py
```

The current 99-file Pump snapshot remains identical to base, digest
`889f4c6595381c3cb5de70398d09d073cf4365359f212f5c4ac05e0e6b107a43`. No program,
builder, SDK or compiler source changes, build, VM, ELF result, byte-match
gain or whole-environment assurance is claimed. The parent packet supplies
the unchanged official host-tool provenance. Final required-gate results and
public/source mapping are reported separately in the PR.
