# Workflow shell stdin input modes

Base: `963d1eefbed3a81a51d2d52f80026c5434a7a423`.
Scope: deterministic build-workflow input inspection in
`scripts/check_workflow_inputs.py`; no program source or captured bytes change.

The literal command `bash -s -- scripts/not-a-file.sh < /dev/null` reads commands
from stdin. The path following `--` is a positional parameter, not a script to
open. Both native bash and sh return zero for this invocation with empty stdin,
even though the path does not exist. Before this fix the workflow checker counts
it as a script dependency and its actual `--all` CLI returns one with a missing
file. This can reject an otherwise valid on-chain reconstruction workflow.

Recognize shell `s` alongside `c` as a non-file input mode, including clustered
flags such as `-es`. Stop inspecting a cluster at value-taking `o`/`O` options;
option-name letters must not become command/stdin flags. Existing `--`, rc-file
options, Python interpreter handling and literal file-mode checks are preserved.
This remains a bounded literal-command inspector, not a general shell parser.

## Reproduction and checks

From the repository root on Ubuntu with Python 3.12.3, Git and PyYAML:

```sh
git show 963d1eef:scripts/check_workflow_inputs.py > /tmp/workflow-checker-before.py
python3 research/tooling-workflow-shell-stdin-20261031/reproduce.py --checker /tmp/workflow-checker-before.py
python3 research/tooling-workflow-shell-stdin-20261031/reproduce.py
python3 -m unittest discover -s scripts -p 'test_workflow_*.py' -v
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
```

`before.json` and `after.json` retain observed checker output and real bash/sh
controls. The focused suite has four methods; applying the new tests to the
base checker produced 17 assertion failures. With the fix all four pass under
native POSIX shells. Controls also cover valid `-o posix`, `-o noclobber`,
`-O extglob`, rc-file options, `-c` precedence, and literal script mode.

The broader required checks use the pre-existing local Python environment that
contains the repository's Solana dependencies; focused parser checks use the
system PyYAML environment. See `validation.json` for exact outcomes and limits.
No dependency installation, capture, chain interaction, captured program
execution, source build, match-score improvement, or hosted CI result is claimed.

Open PR #3245 changes heredoc and `env` parsing. Its diff does not address shell
stdin mode; the changes here are limited to interpreter-option parsing. Live
searches for workflow stdin / shell-options work found no duplicate at selection.
