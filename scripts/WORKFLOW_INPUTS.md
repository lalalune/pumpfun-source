# Workflow script input guard

Run before pushing a feature branch (Python 3.12):

```sh
python -m pip install PyYAML==6.0.3
python -B scripts/test_workflow_inputs.py
python -B scripts/check_workflow_inputs.py --base origin/main
```

The working tree, including untracked workflows, is inspected by default. Use
`--head HEAD` to inspect only committed content, or `--all` instead of `--base`
for a full audit. Fetch the intended base before comparing. Output is JSON;
exit 1 means newly missing inputs, exit 2 means inspection failed.

The guard parses YAML without executing workflow commands. It checks standalone
literal Python/bash/sh script invocations under `scripts/`, `research/`, and
`reconstruction/`, including matrix include command blocks, static matrix axes,
and workflow/job/step working-directory defaults. A removed script still referenced
by an unchanged workflow is a regression. Removing both the obsolete workflow
reference and its script is allowed.

Existing missing references are compared by (workflow, job, path) and printed in
`existing_missing`; they are not described as passing verification. This allows
adoption while the historical evidence matrix is being repaired, without a static
allowlist that could hide future deletions of restored scripts. At base `9f9d94c`,
the initial audit found 277 existing missing references. No workflow is silently
skipped or disabled by this guard.

CI runs on pushes, pull requests, and manual dispatch without path filters (a
script-only deletion must trigger it). PRs compare with the PR base SHA; existing
branch pushes compare with the previous tip; new branches/manual runs compare with
the merge base against origin/main. Full history is checked out. A missing base
object fails inspection. The JSON audit is uploaded even when new inputs fail.

## Scope and limits

This is a static guard, not a shell interpreter, workflow schema validator, or
runtime-equivalence test. Module/inline Python (`-m`, `-c`), generated/downloaded
files outside the three source roots, expression-based matrices, compound shell
commands, shell functions, heredoc bodies, and runtime dependencies are outside
its guarantees. Dynamic or outside-root interpreter inputs encountered are listed
as `uninspected`. It does not prove a generated file will exist. If a workflow
generates a script inside a checked source root, move that generated artifact to
an explicit build-output directory or extend the checker with reviewed provenance;
do not add a blanket missing-file skip.

The guard reports every missing literal reference in `--all` mode. Repairing or
retiring the historical suites remains separate work. It does not replace running
the actual workflows, and it does not coordinate job ordering: the small guard
runs alongside other workflows and gives an early, focused failure report.
