# Research packet revalidation qualification

This package is a source-bound successor to the frozen
`scripts/revalidate_all.py`. It reuses the reviewed script's retained manifest
formats, `check_manifest()` implementation, and packet invocation registry. It
changes only the lifecycle around those checks:

1. record the complete packet identity;
2. check the manifest;
3. execute `verify.py` under a bounded process supervisor;
4. record the complete packet identity again;
5. recheck the manifest;
6. publish a complete, self-verified audit directory with one rename.

The exact reviewed root source is pinned as SHA-256
`2d037c093e69a94c8a9f9c78a01a671506dd2c9f4fb50f603e752caf249c622a`.
The adapter refuses to execute if those bytes change. This binding includes the retained manifest formats, path admission, UTF-8/LF
report writer, and atomic no-replace publication helper. The adapter executes
the bytes it checked and binds its source receipt to that same digest.

The current binding includes the bounded whole-character prefix in the root
runner's standalone temporary-directory helper. This reviewed naming-only
transition leaves its manifest checks and publication semantics unchanged.
Historical packets and their recorded source hashes are retained unchanged;
the adapter still rejects any other unreviewed root-script bytes.

The adapter also bounds its own readable lock and staging basename prefixes to 64
filesystem-encoded bytes, retaining whole characters. Truncated prefixes carry
the SHA-256 of the complete output basename, so different long destinations
sharing a prefix keep separate locks. The final output name is unchanged.
This completes the adapter-specific naming path left outside the root-runner
temporary-name fix in [#3035](https://github.com/lalalune/pumpfun-source/pull/3035).
The real CLI proof and existing-output/cleanup controls are recorded in
[the output-name reproduction](../../../research/qualified-audit-output-names-20261101/README.md).

## Reproduced defects

The focused tests run the actual frozen CLI and real subprocesses.

### Verify-time mutation can pass

A synthetic packet seals `artifact.txt` and `verify.py` in a valid manifest.
The verifier replaces `artifact.txt` and exits zero. The frozen CLI reports:

```text
manifest_check.status = pass
verify_check.status   = pass
overall               = pass
post-run artifact     = not the admitted SHA-256
```

The qualified adapter records pre/post inventories, reruns the manifest check,
and reports both `input_check.status = packet_mutated` and `overall = fail`.
Every regular packet file is recorded by path, byte count, and SHA-256 in
`inputs.json`; directories are recorded by path, and links are recorded by path
and link target without following them.

### Exited verifier leaders can hang the frozen runner

A real verifier leader spawns a detached descendant that inherits stdout and
then exits. The frozen `subprocess.run(capture_output=True)` caller did not
return before an external 1.2-second watchdog. The fixture then killed and
reaped every recorded process.

The adapter redirects stdout/stderr to a private regular file instead of a
pipe, starts each verifier in a new process group/session, applies an explicit
deadline, and bounds cleanup. It returns immediately when a leader exits even
if an escaped descendant retains the inherited output descriptor. For a timed
out verifier it terminates same-group descendants and retains the output tail,
byte count, SHA-256, truncation flag, command, return code, and elapsed time.

### Complete publication preserves prior and late destinations

The currently pinned root runner already stages complete reports, refuses an
existing destination before running verifiers, and uses atomic no-replace
publication. Failed packet checks still produce a complete report with failure
rows. Older root revisions could leave a partial destination after failed
report generation; the qualification no longer attributes that defect to this
pinned revision.

The adapter uses the same pinned native no-replace helper at final publication,
including when another writer creates an empty destination after its precheck.

The adapter:

- refuses an existing destination before any verifier runs;
- snapshots the packet census before creating output parents or staging;
- rejects linked output path components and nondirectory parents;
- writes into a private sibling staging directory;
- writes the manifest last and independently verifies every staged member;
- renames the complete directory to the final destination;
- removes the staging directory and lock after write failures or interruption.

Earlier reports are never replaced. Packet failures still produce a completed
audit report; only audit generation/integrity failures prevent publication.

## Audit provenance

The published directory contains the existing report members plus two bounded
provenance records:

- `inputs.json`: complete before/after inventories and changed paths for every
  packet;
- `provenance.json`: reviewed root source identity, adapter identity/version,
  repository HEAD, interpreter identity, platform, deadlines, UTC bounds, and
  exact packet census.

The adapter and reviewed source are hashed before and after all verifiers; a
change aborts publication.

`results.json` includes the pre/post manifest results, verifier command and
status, output identity, pre/post packet summaries, changed paths, and final
status. The generated `verify.py` checks the exact report-member inventory,
every saved member hash, internal result counts, and provenance schema.

## Run

From the repository root with Python 3.12 or another supported Python 3:

```sh
python -B reconstruction/tooling/revalidation-qualification/audit.py \
  --repo . \
  --output /tmp/pump-revalidation-audit

python -B /tmp/pump-revalidation-audit/verify.py

python -B -m unittest -v \
  reconstruction/tooling/revalidation-qualification/test_audit.py
```

The production verifier deadline remains 60 seconds with a one-second cleanup
budget. Tests use shorter explicit deadlines.

## Relationship to prior work

- #1362 requires all available packet checks to pass.
- #1382 preserves existing outputs and excludes a new audit from its census.
- #1709 supplies the documented repository argument to four retained packets.
- #1721 supports the two retained manifest formats.
- #2088 provides a separate reviewed-source manifest-admission diagnostic.
- The pinned root checker includes manifest path containment.

This package delegates path and digest checks to the pinned
root `check_manifest()` and adds duplicate-JSON-field rejection. When that reviewed source changes, the pin
must be intentionally reviewed and updated before this adapter will run.

## Limits

- This is not a process or filesystem sandbox. On POSIX, descendants remaining
  in the verifier's original process group are terminated. A descendant that
  deliberately creates another session is not claimed to be discoverable or
  killable; file-backed capture prevents it from blocking audit completion.
- Windows can terminate the verifier leader but does not receive a Job Object
  from the Python standard library, so descendant cleanup is weaker there.
- Pre/post identities detect final packet mutation but do not eliminate races
  while a verifier is reading or writing files.
- The sibling lock coordinates adapter writers; the pinned native helper refuses
  a late destination on supported platforms and fails closed where atomic
  no-replace directory publication is unavailable.
- Manifest consistency does not prove authorship, semantic correctness,
  original program equivalence, or cryptographic trust in the manifest author.
- No on-chain program source, compiler input, candidate ELF, scorer, or frozen
  research packet is changed by this package.

The reviewed current root identity also includes explicit duplicate-member
rejection in newly emitted audit verifiers. The qualified adapter's own emitted
verifier follows the same rule. This template-only transition leaves input
manifest admission, process supervision and audit verdicts unchanged; existing
archived audit packets retain their original verifier bytes and source hashes.
