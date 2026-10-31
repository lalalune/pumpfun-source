# Preserve competing disassembly output directories

Base revision: `9120883a957d7d9b2cab6140f66fb5bc9e6774d5`.

`scripts/disassemble.py` refuses an existing output at startup, then disassembles
all selected programs into a private staging directory. Its final ordinary
POSIX rename can replace a competing empty directory created after that check.
The command reports success even though the other writer's directory inode has
been removed. Nonempty competing directories already make the rename fail.

Use the existing `deep_disassembly.rename_directory` helper for atomic
no-replace publication. The helper already supplies native Linux/macOS behavior
and Windows no-replace rename, and fails closed on unsupported hosts. There is
no separate existence-check race and no new publication implementation.

The regression runs the production CLI in an isolated source tree. System `cc`
compiles an authored native C fixture; a forwarding launcher creates a competing
directory during the tool invocation, then executes the real system `objdump`.
The test checks actual disassembly of `proof_value`, input/output manifest
digests, the competing directory's inode and contents, and staging cleanup.
Neither compiler nor disassembler results are fabricated.

| Destination during actual disassembly | Base | Fixed |
| --- | --- | --- |
| Remains absent | Complete bound packet published | Complete bound packet published |
| Competing empty directory | Exits 0; competing inode replaced | Exits 1; same empty directory retained |
| Competing nonempty directory | Exits 1; file and inode retained | Exits 1; file and inode retained |

`before.json` and `after.json` retain these observations. `proof.json` binds the
tested source, regression, observations, and installed compiler/disassembler
versions. Temporary roots and Python installation prefixes are redacted from
exception traces. All fixture ELF hashes agree between the six cases.

Repeat with installed Linux `cc` and `objdump`:

```sh
python3 -B scripts/test_disassemble_no_replace.py -v
python3 -B scripts/test_disassemble_no_replace.py --probe
python3 -B -m unittest discover -s scripts -p 'test_disassemble_*.py' -v
```

To repeat the base behavior, create a separate worktree at the pinned base,
copy only `test_disassemble_no_replace.py` into its `scripts/` directory and run
the same test/probe there. The test fails on the empty-directory case on base;
the probe reports observations without enforcing the fixed expectation. CI runs
the new regression alongside the existing disassembly-publication checks.

Validation: all 17 disassembly regressions pass, all 250 tooling tests pass,
and all nine retained captures verify. The same new regression fails on base
because the empty-directory race succeeds and replaces the competing inode.

Limits: this is publication behavior measured with actual native disassembly,
not disassembly validation of a maintained SBF program, a fresh SBF build,
new bytecode matches, runtime equivalence or security acceptance. All retained
captures, prior packets, program source and scoring rules are unchanged.
