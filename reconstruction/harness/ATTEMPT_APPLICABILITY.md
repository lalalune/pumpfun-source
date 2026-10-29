# Reusing earlier experimental findings

Use an explicit saved ledger, never the live ledger implicitly:

`python reconstruction/harness/attempt_applicability.py --ledger ATTEMPTS.jsonl --context current.json --evidence-root /evidence --target 0x14f4e0 --approach exact-recorded-approach`

The current context is a JSON object containing five lowercase SHA-256 fields: `source_sha256`, `toolchain_sha256`, `original_sha256`, `inventory_sha256`, `command_sha256`. Use a canonical source manifest, full toolchain manifest and canonical command/flags/environment manifest as the corresponding hash inputs. Keep those manifests in the evidence set. A revision label or arbitrary dedupe key is not a substitute for content hashes.

For newly recorded attempts, the existing ledger's --data JSON may contain:

```
{
  "context": {"source_sha256": "...", "toolchain_sha256": "...",
              "original_sha256": "...", "inventory_sha256": "...", "command_sha256": "..."},
  "evidence": [{"path": "trial/verdict.json", "sha256": "..."}]
}
```

Replace ellipses with actual hashes. Paths must be relative to --evidence-root. The inspector does not add these fields to historical records or derive missing identities from prose. It selects the exact approach and numerically equal address target (or exact named scope such as `all`), preserving the recorded status/hypothesis for interpretation.

- **compatible**: all five recorded identities agree and every declared evidence file is present with the expected hash.
- **stale**: at least one recorded identity differs; changed field names are reported.
- **unverifiable**: context/evidence is missing, malformed or no longer verifiable. Old records without the new optional metadata fall here, not into “already tried.”

Compatibility authenticates internal consistency of the declared record, not its author, completeness, reproducibility or conclusion. It does not imply semantic equivalence between differently named approaches. A compile-failed record is still compile-failed, not proof that a source strategy cannot match. Changed source/toolchain contexts may justify rerunning an earlier negative experiment. Missing metadata is not a reason to discard historical notes.

The command reads without locking/writing the live ledger, executing binaries or fetching URLs. Use a saved snapshot if another process is appending. Duplicate JSON fields and malformed rows are reported with line numbers and cause exit 2; selected rows still appear. This is complementary to the stricter ledger-wide schema audit in #1409.
