# Resumable, bounded experiments

Source/output separation checks existing filesystem identities as well as
resolved paths, including alternate case spellings on case-insensitive volumes.
Result/input collision checks likewise include existing physical aliases while
retaining resolved-path checks for destinations that do not yet exist.

`python reconstruction/harness/experiment_runner.py matrix.json --out /tmp/trials --max-trials 20`

A matrix is a JSON array of objects with unique simple `name`, absolute `source` directory, `command` argv array, optional `inputs` file paths and `timeout` seconds (default 300, maximum 86400). Use `{source}`, `{work}` and `{out}` in arguments. Commands run sequentially in an isolated working directory, without a shell. Source is copied; `.git`, `__pycache__` and the source root's `target` directory are omitted. A regular file named `target` and nested `target` directories remain source inputs. Source symlinks and special files are refused. The output tree must be separate from the source.

The command contract is exit 0 = predicate holds, 1 = valid experiment but predicate does not hold, other status/timeout = infrastructure error. A compiler failure must not be converted into exit 1. `match_oracle.py` implements this contract for one official raw/normalized Pump window, including stack-warning rejection and isolated original-window cache. Example command array:

```
["/absolute/python3.12", "/absolute/repo/reconstruction/harness/match_oracle.py",
 "--source", "{source}", "--work", "{work}", "--out", "{out}",
 "--sdk", "/absolute/platform-tools", "--hybrid", "/absolute/hybrid144",
 "--window", "0x14f4e0", "--kind", "normalized"]
```

For this example `source` is the Pump crate directory, not the repository root. The existing Cargo dependency cache must be provisioned; builds are offline. Set timeouts appropriate for cold builds. No warm template is seeded by this oracle.

Declare every relevant external input in `inputs`: oracle/harness scripts, original ELF, window inventory, toolchain executables/libraries and any configuration consumed by your command. Resume identity includes source file bytes/executable bits and directory membership, argv, declared input bytes and execute permission bits, command executable, timeout, environment hash and runner implementation. Environment values are not recorded. Undeclared files, network responses and changing external services are not authenticated: this is not hermetic execution or a sandbox. The source snapshot and declared inputs are checked again after execution.

Each attempt retains stdout/stderr and all output files, with hashes in latest.json. A trial's `latest.json` must not resolve to a declared input of that trial or any other matrix row; the whole matrix is checked before any command starts. Output directory membership, including empty directories, is also recorded. Resume reuses only pass/fail results whose identity and retained artifacts still match. Reuse also requires the current result schema, an exact integer exit/status pair (0/pass or 1/fail), no error reason, and saved input provenance that matches both current admission and its cache key. Inconsistent result metadata retries in a new attempt directory, like an invalid artifact record; prior attempts remain. Errors also retry. A per-trial file lock serializes concurrent users of the same destination. Result hashes are integrity checks, not signatures or tamper-proof provenance. A matrix exits 2 on infrastructure error; valid failing predicates remain useful results and do not fail the matrix driver.

## Process cleanup and runner death

Every trial runs in a process group led by a small guardian. The experiment
runner owns the guardian through a close-on-exec control pipe. Normal exits
preserve the command's exact integer return code. Timeouts and Python-level
interruptions close that pipe and request bounded cleanup. The guardian kills
its own group on normal command completion as well as on EOF or a status-write
failure, including ordinary grandchildren. A stopped guardian is killed only
after checking that its live, unreaped PID still owns the group. A reaped
guardian or historical trial PID is never used to authorize a later signal.
If the runner receives SIGTERM or SIGKILL, the pipe closes and the guardian
kills its own group. The guardian
source bytes are compiled directly and frozen at runner import time; a cached
bytecode file cannot substitute for those admitted bytes. Their hash
participates in the experiment identity.

This composes with, and does not replace, `build_process.py`'s compiler
guardian added by PR #3339. The outer guardian stops the trial group; the
compiler guardian still stops the nested compiler session if the trial itself
is killed. A process that deliberately calls `setsid`, double-forks, or is
otherwise detached can escape both ordinary process groups. The system also
cannot guarantee cleanup if the guardian itself is independently SIGKILLed.
Whole-machine crashes are subject to filesystem and
hardware durability. These are supervision guarantees, not a sandbox.

## Interrupted attempts and recovery

Every `attempt-*` directory has an `attempt.json` with the admitted input
identity and one of these states:

- `staging` or `running`: no result is admissible; a later locked invocation
  marks the attempt `interrupted` after its owned group is gone;
- `interrupted`: partial stdout, stderr and output hashes are retained as
  evidence, but never reused as a result;
- `completed`: the result receipt and artifact hashes were synced, but publication may have been
  interrupted before `latest.json`; a matching attempt is fully revalidated
  before that pointer is repaired;
- `published`: publication completed. Historical published attempts remain
  immutable and only the currently admitted `latest.json` is reused.

Attempt and latest receipts are written through an fsynced temporary file,
atomically replaced, then followed by a directory fsync. Invalid JSON, invalid
identity hashes and contradictory result metadata are never accepted. A
superseded or corrupt regular `latest.json` is copied byte-for-byte into
`receipt-history/` before replacement. Existing attempt directories are not
deleted. The output lock ensures concurrent callers perform at most one retry;
later callers revalidate and reuse that result.

Inspect a retained destination without changing it:

```bash
find /tmp/trials -name attempt.json -o -name latest.json -o -path '*/receipt-history/*'
python3 -m json.tool /tmp/trials/TRIAL/attempt-UUID/attempt.json
```

To resume an interrupted matrix, rerun the same command with the same matrix
and `--out`. The runner re-hashes the source, executable, declared inputs,
execute bits, environment, runner and supervisor. Same-identity interrupted
attempts retry in a new directory; changed identities are explicitly recorded
as nonmatching and also retry. Do not edit an interrupted receipt to make it
look completed.

The bounded process and recovery regressions do not require a Solana build:

```bash
python3 -I -B reconstruction/harness/test_process_supervisor.py -v
python3 -I -B reconstruction/harness/test_experiment_runner_parent_death.py -v
python3 -I -B reconstruction/harness/test_experiment_recovery.py -v
```

Tool aliases are resolved once during admission. The recorded `executable` is
hashed and executed; `invocation` preserves the declared absolute argv[0] for
virtual environments and rustup proxies. Switching an alias after admission
does not select another binary. The changed runner identity invalidates older
cache keys while retaining previous attempt directories.
The argument array and child environment are also captured at admission, so
caller mutations during staging or lock waits cannot execute a different trial
under an old cache key. Environment values remain unrecorded; only their hash
appears in the receipt.
Declared input paths retain their resolved targets as well as content hashes
and owner/group/other execute permission bits (`st_mode & 0o111`);
retargeting an input alias or changing its bytes or execute bits before launch is rejected, and
post-run checks reject changes still present at the end of execution. These
checks do not protect against inputs changed and restored between checks.
Execute bits are recorded separately from the existing content-hash map. The
changed runner fingerprint invalidates earlier cache keys without changing
historical attempts. Read/write permission bits, ownership and ACLs are not
part of this execute-bit identity.
The runner fingerprint is captured at import time; later edits to the driver
on disk cannot relabel that import-time fingerprint. It is not an immutable
snapshot of every executable or script byte read during the child process.

## Locate a first-parent regression

`python reconstruction/harness/bisect_membership.py --repo /repo --good GOOD_SHA --bad BAD_SHA --source-subdir programs/pump --oracle oracle.json --out /tmp/bisect --max-trials 20`

The oracle JSON contains the same `command`, `inputs` and `timeout` fields as a matrix row. The result path `--out/bisect.json` must be separate from the oracle configuration and its declared inputs; resolved collisions are rejected before trials begin. Both endpoints are evaluated. Only pass/fail move bounds; build errors are skipped and can leave an unresolved interval. Archived source links remain unsupported and are recorded as unknown revisions in `archive_errors`; they are never extracted or passed to the oracle. The first-parent chain must contain the good endpoint. Source comes from git archives in temporary directories; no checkout, branch or index is changed. The report identifies adjacent passing/failing revisions only when qualified, and otherwise lists the possible first failures. The binary-search inference assumes a monotonic transition; it does not prove no later recovery or a unique causal commit across a merge's other parents.

## Minimize an ordered patch set

`python reconstruction/harness/minimize_experiment.py --source /base/crate --patches patches.json --oracle oracle.json --out /tmp/reduce --want pass --max-trials 30`

`patches.json` is an array of absolute paths to independently supplied patch units. Units may be files or carefully prepared hunks; the tool does not guess how to split a diff. Selected units are always applied in original order in a disposable git-initialized source copy. Application failures are infrastructure errors, with diagnostics retained in the report. --want fail searches for a valid nonmatching build; compilation failures never count as reproducing a loss.

The algorithm removes groups, then checks individual removals. `one_minimal` means no single remaining unit can be removed while retaining the predicate, under the completed tests. It does not mean globally smallest. Exhausted budgets or untestable removals report bounded results without claiming minimality. An empty result means the unmodified base already has the requested property. Source and output trees must be separate. The result path `--out/minimized.json` must also be separate from supplied patch files, the patch-list manifest, the oracle configuration and its declared inputs; a collision is rejected before trials begin. Reports include source/patch hashes and tested subsets; original source and patch files are never edited. Use the selected indices to construct the final proposed source change and rerun full no-loss validation; a one-window predicate alone is insufficient for PR acceptance.

### Preserve existing matches during target searches

Pass `--baseline /absolute/path/to/control-score.json` to `match_oracle.py`
when a target search must also preserve every control normalized and raw
membership. The oracle snapshots and hashes the report before compilation and
requires the same original inventory and window sizes. A target match with any
membership loss is exit 1 (`fail`), with the full preservation comparison in
`verdict.json`; invalid baseline inputs are exit 2. A target match with all
memberships preserved is exit 0. Without this option, the existing target-only
predicate remains available for exploratory searches.

When used through the matrix, minimizer or bisection runner, include the baseline
file in the oracle configuration's `inputs` list so its content participates in
trial reuse identity. This gate does not establish runtime equivalence.
