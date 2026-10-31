# Saved-score and diagnostic report publication

Base: `9120883a957d7d9b2cab6140f66fb5bc9e6774d5`.

`compare_scores.py` opens its final `--json` destination before writing. A
failed write leaves a partial comparison receipt, and the command's intended
exclusive-create behavior then prevents the same command from retrying.

The probe runs the actual standalone CLI with the two retained baseline
reports, each containing 1,035 windows. It sets a 64-byte file-size limit in
the child only, then repeats the identical command without that limit. It
does not change the input reports, invent score rows or run a program/build.

| Actual CLI scenario | Base | Fixed |
| --- | --- | --- |
| Limited write | exit 2; 64-byte partial report | exit 2; no report or staging file |
| Same-command unlimited retry | exit 2; existing partial blocks retry | exit 0; complete 274-byte report |
| Separate unlimited output | exit 0 | exit 0; identical JSON bytes |
| Existing receipt destination | exit 2; retained | exit 2; retained |
| Either input as destination | exit 2; retained | exit 2; retained |

The fix stages the complete text in the destination directory, flushes,
fsyncs and closes it, then publishes it exclusively. POSIX uses a hard link; Windows uses its
non-replacing rename. An existing or concurrently created destination is
never replaced. Cleanup removes only the staging file created by this call.
Normal umask-derived modes and existing comparison/exit-status rules remain.

Reproduce on POSIX:

```sh
python -B research/runtime-score-publication-20261101/probe.py . \
  --revision 9120883a957d7d9b2cab6140f66fb5bc9e6774d5
python -B research/runtime-score-publication-20261101/probe.py .
python -B tests/test_compare_scores_publication.py
python -B -m unittest discover -s reconstruction/harness -p 'test_compare_scores*.py'
python -B scripts/test_tooling.py
python -B scripts/verify_evidence.py
```

`--revision` copies only the reviewed, standalone comparison script from Git
into an owned temporary directory. Inputs come from the selected checkout;
the probe records their hashes and verifies they remain unchanged. The proof
and fixed tests ran on macOS/Python 3.12.13. Three new tests and eleven
existing comparison tests pass, along with 250 tooling tests and all nine
captured-evidence checks. One new test also injects a competing writer at
publication to check exclusive creation; the failure/retry proof itself uses
real filesystem errors and actual CLI processes, without mocks.

This qualifies local report publication, not a new score or program match.
The limit test is explicitly skipped where POSIX file-size limits are
unavailable; native Windows execution and filesystems without hard-link
support were not qualified. No crash/power-loss durability claim is made.

## Same-cause diagnostic consumers

`control_flow.py` and `target_metric.py` used the same direct exclusive-write
pattern. They now call the existing `compare_scores.publish_report` helper;
the standalone saved-score probe remains self-contained. This is one grouped
publication fix, with no changes to instruction analysis, ranking or scoring.

`diagnostic_probe.py` runs both actual CLIs, with the original Pump ELF and
the retained multihop candidate's compressed symbol ELF. The control-flow
range is the existing 176-byte window at address 288. The metric selects the
retained `try_accounts` symbol for that window. No binary is executed, built
or altered; the symbol ELF is decompressed into an owned temporary file.

| Diagnostic | Base limited write / retry | Fixed limited write / retry | Unchanged complete output |
| --- | --- | --- | --- |
| `control_flow.py` | 64 bytes; exit 2 / 2 | no output; exit 2 / 0 | 1,319 bytes |
| `target_metric.py` | 64 bytes; exit 2 / 2 | no output; exit 2 / 0 | 787 bytes |

Existing report and binary-alias destinations remain untouched, and no
staging files remain after failure. The probe records exact CLI, dependency,
inventory and input hashes. Its `--revision` mode copies the chosen CLI only;
the unchanged harness dependencies come from the checkout and are hashed.

```sh
python -B research/runtime-score-publication-20261101/diagnostic_probe.py . \
  --revision 9120883a957d7d9b2cab6140f66fb5bc9e6774d5
python -B research/runtime-score-publication-20261101/diagnostic_probe.py .
python -B tests/test_diagnostic_report_publication.py
```

Two additional test methods exercise both real diagnostic CLIs. Final
affected-suite and mandatory gate counts for the grouped patch are recorded
in `results.json`; the earlier three-test saved-score result above remains
the original bounded proof, not the total after grouping.
