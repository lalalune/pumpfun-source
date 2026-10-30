# Workflow lint gate

`lint-workflows.yml` runs on pull requests that change `.github/workflows/`,
pushes to `main` that change those files, and manual dispatches. It checks all
workflow YAML files with `actionlint` v1.7.12, including expression contexts and
workflow keys. The runner downloads the upstream Linux amd64 release and checks
the archive against the SHA-256 fixed in the workflow before executing it. The
checkout token is read-only and not persisted.

To reproduce locally, install the same release from
https://github.com/rhysd/actionlint/releases/tag/v1.7.12 and run from the
repository root:

```sh
actionlint -shellcheck= -pyflakes=
```

Those flags keep this gate focused on workflow syntax and expressions. It does
not execute jobs, validate referenced research scripts, or replace the existing
reconstruction and evidence checks. The missing-script guard in PR #1447 covers
a different failure class; retirement PRs #1432 and #1459 address obsolete
workflows whose entrypoints have already disappeared.
