# Paired-build case-alias output preflight

`BUILD_SCORE_PAIR.md` requires the output to be disjoint from both Pump source
trees, including directory aliases, before any scoring inputs or receipts are
written. The coordinator used lexical ancestry after `Path.resolve()`. On a
case-insensitive macOS filesystem, resolve can retain alternate case spelling:
`--base .../case-base --out .../CASE-BASE/programs/pump/new-evidence` bypassed
that check. The coordinator created the output and copied scoring inputs into
the clean source tree before failing later at SDK admission. Existing source
file bytes were preserved, but the new files changed the source inventory.

Reuse `fastbuild.contains_path()` in both directions before source admission
or output creation. It checks physical ancestor identity, including existing
ancestors of an output that does not exist yet. This extends the coordinator's
existing guard without changing compilation, scoring or source receipt rules.

## Actual macOS observations

Base main: `8330455eb0897493714da67aa4de6f9743d82b84`.

| | Before | After |
| --- | --- | --- |
| Exact tested revision | `d14536ff3a54f3387757c672570f957f81ecfde9` | `650756326928eb8fdedb8161fc632075bf95059b` |
| Successful workflow | [41282982928](https://github.com/miracle2044/pumpfun-source/actions/runs/41282982928) | [41283174088](https://github.com/miracle2044/pumpfun-source/actions/runs/41283174088) |
| Output under case alias of base source | creates scoring inputs | rejected before writes |
| Output under case alias of candidate source | creates scoring inputs | rejected before writes |
| Lexical, symlink and ancestor controls | rejected; sources unchanged | same |
| Disjoint output control | reaches missing-SDK admission; sources unchanged | same |

The same `reproduce.py` runs six real CLI scenarios on each revision. It copies
the actual selected Pump crate into owned clean Git checkouts and requires
complete source snapshots to match the original. Actual filesystem `samefile`
checks establish that the alternate spellings name the same directories. No
path, source-admission function, process result, compiler or scorer is mocked.
Before/after source inventories include file bytes, execute bits and directories.

All CLI scenarios intentionally exit 2. The rejection message, copied scoring
input and source snapshots distinguish the bad early writes from correct
preflight. Explicit absent `--sdk`/`--hybrid` paths stop the disjoint control
after admission; no compiler, linker, scorer or target program executes.
This is a source-preservation result, not successful SBF build evidence.

Both hosted runs pass five related test modules, nine capture identities and
256 tooling tests. The modified overlap module runs seven tests after the fix,
including two new actual-CLI case-alias regressions, with no skips on this Mac.
The other modules cover source-root aliases, paired-build boundaries, normal
coordinator behavior and scorer module bindings. Full publication-failure suites
and new source builds were not run.

## Repeat and inspect

On a case-insensitive macOS filesystem with Python 3.12 and pinned requirements:

```sh
python -B research/pair-case-output/reproduce.py
python -B scripts/verify_evidence.py
python -B scripts/test_tooling.py
```

Use a fresh `work/scoped-proof`; the probe refuses existing output and producer
hashes outside `transition.json`. The two observation archives retain commands,
stdout/stderr, exact source snapshots, output observations and related test logs.
Summaries and complete workflow logs are retained separately. `receipt-files.json`
pins every retained file. Offline verification needs only standard Python:

```sh
python -B research/pair-case-output/verify.py
```

No program source, recipe, capture, historical packet, scoring threshold or
acceptance rule changes. The proof is finite preflight evidence and does not
establish binary equivalence, full runtime behavior or security acceptance.
