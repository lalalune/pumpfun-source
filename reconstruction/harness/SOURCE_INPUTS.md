# Source input receipts

Each fastbuild run writes `source-inputs.json` beside its build log and includes
`source_sha256` in its result. The receipt lists relative POSIX paths, file sizes,
executable flags and SHA-256 hashes; its digest covers the canonical sorted list.
Absolute source paths, usernames and filesystem timestamps are not included.

The builder snapshots the input crate before staging and checks it again afterward.
Detected changes stop the trial before compilation, avoiding a build from a mixed
source copy. Keep source editing and staging serialized: these checks are not a
filesystem snapshot or a guarantee against every concurrent-writer race.

Only the real crate-root `target` build directory and Git metadata are excluded.
Nested directories such as `src/target` and `assets/target` are source inputs,
matching the builder's rsync policy. Source symlinks and nonregular files are
rejected, including a directory symlink named `target` at the crate root.
Workspaces cannot overlap the input source, and output cannot be inside it.
Receipts remain available for failed compiler runs as well.

This identifies crate source inputs, not the entire build environment: registry
packages, compiler/toolchain files and environment variables are not covered.
A receipt alone does not prove reproducibility or bytecode equivalence.

`win.py show` disassembles a private copy of the candidate bytes loaded by
`Cand`, and `win.py list` scores such a copy when filtering matched windows.
A rebuild replacing the original candidate path cannot mix new assembly labels
or match memberships with old comparison tokens and symbols. The temporary copy
is removed after successful or failed analysis. This binds diagnostic bytes;
it does not establish source provenance or program equivalence.
