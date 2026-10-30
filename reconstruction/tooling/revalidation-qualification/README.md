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
`3f8e5965ddbebb9ff5947061ceffc4f661d3fc53eea32dbc5352f190c2fbb1b1`.
The adapter refuses to execute if those bytes change. This binding includes
#2522's empty-manifest rejection and #2559's UTF-8/LF packet writes; the adapter
already rejects empty manifests, and the writer change preserves audit content.

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

### Failed generation exposes a partial final directory

The frozen CLI creates the requested final directory before verification. A
synthetic verifier can create `results.json` as a directory; the later report
write fails and leaves that partial final destination in place.

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
- Open #2223 adds manifest path containment to the frozen root checker.

This package deliberately does **not** duplicate #2223. It calls the pinned
root `check_manifest()` unchanged. When that reviewed source changes, the pin
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
- The sibling lock and final existence check protect ordinary single-host
  writers. Atomic no-replace directory rename is not claimed against a hostile
  concurrent filesystem actor on every platform.
- Manifest consistency does not prove authorship, semantic correctness,
  original program equivalence, or cryptographic trust in the manifest author.
- No on-chain program source, compiler input, candidate ELF, scorer, or frozen
  research packet is changed by this package.
