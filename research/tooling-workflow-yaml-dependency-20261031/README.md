# Make the workflow input checker usable with the pinned Python requirements

Base: `963d1eefbed3a81a51d2d52f80026c5434a7a423`.

`scripts/check_workflow_inputs.py` unconditionally imports `yaml`, but the base
requirements install only solders, pyelftools, jsonalias and typing_extensions.
In a new environment containing exactly those requirements, even `--help` fails
with `ModuleNotFoundError: No module named 'yaml'`. A real workflow check cannot
distinguish an existing script from a deleted script because it never starts.

Add `PyYAML==6.0.3`, the version exercised here, and document the dependency.
The existing package versions and the checker source stay unchanged. This is a
Python tooling setup fix, with no program source, captured evidence, score or
runtime reconstruction change.

## Reproduce

Create two independent fresh virtual environments with the same Python. Install
the base requirements in the first and this branch's requirements in the second:

```sh
git show 963d1eefbed3a81a51d2d52f80026c5434a7a423:requirements.txt > before.txt
python -m venv before-env
python -m venv after-env
# Use each environment's Python/pip; Windows puts them under Scripts/.
before-env/bin/python -m pip install --only-binary=:all: -r before.txt
after-env/bin/python -m pip install --only-binary=:all: -r requirements.txt
before-env/bin/python scripts/check_workflow_inputs.py --help
after-env/bin/python scripts/check_workflow_inputs.py --help
```

The measured installation used uv 0.11.14 with Python 3.13.14 on Windows and
binary wheels only. `comparison.json` records actual checker CLI calls against
an isolated Git fixture: `.github/workflows/check.yml` runs `python scripts/ok.py`
(a file containing `pass`), then `python scripts/missing.py` (not present).
The base environment fails at import for both inputs. The fixed environment
returns 0 for the existing file and 1 with the correct missing reference for the
absent file. No workflow body is executed by the checker. All 35 existing
workflow regression tests pass in the fixed environment.

## Verification and limits

See `validation.json` for exact environments, commands and outcomes, including
the required saved-evidence and tooling checks. No program rebuild or score
improvement is claimed. The clean-environment reproduction covers the missing
dependency, not every possible host or package index. Existing stopped runtime
scopes, source checkpoints and original captures are unchanged.
