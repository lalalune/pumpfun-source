# Keep the qualified audit's required members in its standalone verifier

Base: `13fe4536be64d8c5c10f8905e9d2236f423ac4f4`. Scope: offline reconstruction
evidence tooling. No program source, build inputs, captured bytes or scores change.

The maintained qualification adapter validates its fixed `REPORT_MEMBERS` before
publishing an audit. The generated standalone `verify.py` instead compared only
the files currently present with the editable manifest. Removing `inputs.json`
and its manifest entry therefore still produced `verified: true`, despite losing
the complete pre/post input inventories promised by that report format. The same
failure affected the README and the passed/failed/skipped lists.

The regression invokes the real qualified-audit CLI over a fictional sealed
artifact, runs the emitted verifier successfully, removes each required member
and its declaration, then runs that unchanged emitted verifier again. All five
incomplete reports pass before the fix. All five fail after it, while the five
complete controls still pass. No configured program or captured image executes.

The generator now embeds its existing `REPORT_MEMBERS` tuple into the standalone
checker and checks that exact manifest schema. Its existing file/type/hash and
metadata checks remain in place. No frozen revalidator, historical packet, or
source-authorization digest is changed. This differs from prior duplicate-JSON
admission changes: the defect is missing mandatory report components after
publication, not ambiguous incoming packet manifests.

Reproduce from the repository root:

```sh
python3 reconstruction/tooling/revalidation-qualification/test_audit.py AuditTests.test_published_verifier_keeps_the_required_member_inventory -v
python3 -m unittest discover -s reconstruction/tooling/revalidation-qualification -p 'test_*.py' -v
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
```

Observed results: one regression with five failing corruption cases before;
regression passes after; all 62 qualification tests pass; all nine captures
verify; all 228 tooling tests pass. Required checks used the existing pinned
Python dependencies on Ubuntu WSL ext4. Raw commands and result summaries are
retained alongside this note. A retained fixture omitted by the sparse view was
materialized from the same commit before rerunning the qualification tests.

This is completeness and byte-consistency checking. It does not authenticate
authorship, prevent deliberate rewriting of the checker, prove program
equivalence, or establish hosted CI success.
