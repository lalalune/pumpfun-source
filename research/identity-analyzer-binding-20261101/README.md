# Reviewed current analyzer in the identity audit

At `599891304e83e853ec723dc1417550bef4e1c074`, the maintained identity-audit
wrapper rejects every current input tree with `reviewed identity audit source
changed: scripts/analyze.py`. Its active four-method CI suite has three failing
assertions and four subtest errors. The direct identity audit still works.

The source transition is the three-line ELF-header/table extent check in
`97f2f2a625458a3dbe7adf3eab59b2906f66832a`, merged through
[#3813](https://github.com/lalalune/pumpfun-source/pull/3813). It rejects truncated
ELF inputs as `ValueError` before unpacking. Reviewing that complete diff changes
the admitted analyzer digest from `364589223d559a709b48ca56726f4a8f8ad2d1674542a1d94223e1dfbfa0b35d`
to `178a21b4f70d9deb63646d216306a252c08c11aa0b52b2e7df77db85fcffd262`.

Only that fixed source binding changes. This follows the wrapper's documented
reviewed-transition policy and [#3636](https://github.com/lalalune/pumpfun-source/pull/3636).
The analyzer, audit, comparator, captures, historical packets, isolated child
execution and unknown-source rejection remain unchanged. The pin is not learned
from current files at runtime. This is a follow-up integration of the accepted
ELF-validation correction, not a new analyzer algorithm.

## Actual CLI evidence

The proof copies all nine retained captures and the three complete current
helpers into an owned temporary tree. Explicit indexes compare each captured
image with itself; this is a valid audit control, not a rebuilt candidate.
LF/CRLF helper copies each run under normal Python, `-O`, `-OO` and both
`PYTHONOPTIMIZE` settings. Before the fix all ten wrapper runs fail at the stale
pin. Afterward all ten reports are byte-identical to direct current audits,
including the nine input identities and the no-source-completeness/no-historical-
compiler-identity qualifications. Native Windows is not exercised.

Twelve controls retain six changed-source rejections, two occupied-report
preservations and four incorrect original/candidate digest refusals. The latter
now reach the intended hash check instead of failing earlier at the stale pin.
All capture and source inputs remain byte-identical. The public proof uses no
mocked subprocesses, compiler, VM, RPC or program execution.

```sh
python -B research/identity-analyzer-binding-20261101/probe.py --repo . \
  --revision 599891304e83e853ec723dc1417550bef4e1c074 --output work/identity-binding-before.json
python -B research/identity-analyzer-binding-20261101/probe.py --repo . \
  --output work/identity-binding-after.json
python -B reconstruction/diagnostics/identity-audit-unoptimized/test_run.py
```

The proof stages the wrapper at its repository path inside the temporary
tree. The wrapper resolves its default root as `parents[3]`, so a copy at
`<tmp>/wrapper.py` fails at import under a shallow `TMPDIR` such as Linux `/tmp`.
The wrapper always receives an explicit `--repo`, so its placement does not
change any recorded result.

Use fresh output paths and the pinned Python requirements. The base command
needs its local Git revision. The existing CI suite now also runs the complete
nine-capture proof; its prior four methods remain intact. `results.json` binds
the before/after wrapper, helper and capture hashes to these actual runs.
