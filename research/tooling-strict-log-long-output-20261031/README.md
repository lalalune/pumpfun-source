# Strict-log audit publication with a long output name

Source base: `963d1eef` on `lalalune/pumpfun-source/main`. This is an offline
audit-publication fix under CONTRIBUTING.md's reconstruction-tooling scope.
It changes no program source, build input, captured evidence or score.

## Observed failure

`pump_strict_ordered_logs.py` used the entire requested output filename as its
temporary-file prefix, then added punctuation and a random suffix. A valid
255-byte filename on the tested ext4 filesystem therefore failed with
`OSError: [Errno 36] File name too long` after the log audit completed.

The regression first writes and removes the exact final path as a filesystem
control. It then invokes the real CLI with the retained set-params rejection
logs and the captured original Pump image as both sides of an identical-image
control. The same command fails on the base and publishes the bound receipt
after the fix. It also checks refusal to replace an existing receipt, no staging
leak, and byte-for-byte unchanged inputs. The captured image is read, not run.
This is not a rebuilt candidate or a new runtime-coverage claim.

The fix uses a short fixed staging prefix in the same destination directory.
Exclusive temporary creation, input rechecks, no-replace publication and cleanup
remain the existing implementation. The new regression is in the existing
CI-invoked `test_pump_strict_ordered_logs_output.py`.

## Reproduce

From the repository root with the pinned Python requirements installed:

```sh
python3 -m unittest discover -s scripts -p 'test_pump_strict_ordered_logs*.py' -v
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
```

The before run uses the unchanged base auditor with the new test. Its only
failure is the real CLI's filename-component overflow. The focused after run
passes 22 tests. Required-check outcomes and exact input identities are recorded
in `results.json`. Logs replace the checkout root with `<repo>` and the home
prefix with `<home>`. No hosted CI or target compilation result is claimed.

The initial WSL run from the Windows mount also exposed the existing filesystem
limit of `renameat2` packet publication and missing sparse-checkout inputs.
Required checks were repeated on an ext4 validation view using the same base
and unchanged, committed missing inputs. No unrelated verifier was changed.

The test deliberately uses POSIX `PC_NAME_MAX`; it skips on Windows rather than
claiming a Windows path-length result. Existing publication tests still cover
the Windows no-replace code path. Acceptance and any reward remain maintainer
decisions.
