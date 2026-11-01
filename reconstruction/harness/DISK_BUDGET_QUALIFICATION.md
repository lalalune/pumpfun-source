# Disk-budget qualification — 2026-11-01

The gap was audited at
`e89d79aa8d0ad61cefa99b614390eca13500a743` and the completed branch was
integrated with upstream `4b6fc7177b70de6ba6c155a1b3585fa5622ed374`.
No on-chain program source, captured evidence, scorer rule, cache or existing
worktree was modified or removed by this work.

## Before/after reproduction

A bounded probe loaded `fastbuild.py` from the audited upstream commit and the
fixed module, injected the same zero-available-byte `statvfs` result, and
replaced the expensive build body with a marker:

```json
{"after":{"candidate_published":false,"entered_build_body":false,"failure_classification":"resource_budget_exceeded","ok":false},"base_sha":"e89d79aa8d0ad61cefa99b614390eca13500a743","before":{"entered_build_body":true,"result":{"ok":true}},"mock_available_bytes":0}
```

The base entered its build body because it had no storage admission. The fixed
path rejected before staging. This probe allocated no filler data.

The real CLI was also run with an intentionally impossible floor. It rejected
before staging with 64,246,386,688 measured available bytes, published no
candidate, and produced independently accepted receipt SHA-256
`a4a1959151737e6c3d366373d499681f03affc954d7a17ac787b288e761f5693`.

## Pinned build acceptance

One cold identity build and one warm final-code confirmation were run serially
with a 20 GiB floor. The warm confirmation is the final qualification:

- source SHA-256: `958d63ecb3eefb200a17e88ca34d6c8558f27fda5dbe45d18df1880707a3e6e5`
- recipe/triple: `identity` / `sbpf-solana-solana`
- duration: 12.4 seconds
- observations: 18
- floor: 21,474,836,480 bytes
- minimum observed: 63,985,799,168 bytes
- guard fired: no
- runtime-valid: yes; zero stack warnings
- unstripped SHA-256: `54344822ddef0bd4b1f7b4e8a6c80e5aae7e7fb804c5c82c67e7ebff369e9229`
- candidate SHA-256: `6f439f1e539ec8156aba443e9a464eedee0996c88720b3eae789e148e4fef7be`
- resource receipt SHA-256: `7190dd8a3f57866f6c9aaf7fca45aa03049ae4948b2f1c1fbe1041b96c1296eb`
- retained log: `real-build-out/build.log`
- candidate published: yes
- prior successful candidate preserved under `real-build-out/previous/build-*`: yes

The cold and warm executions produced identical candidate and unstripped
hashes. Toolchain hashes, source identity, harness hashes, observations,
publication state and the retained log path are embedded in the resource
receipt. `resource_budget.py` independently accepted it.

Local retained evidence is under
`~/.cache/pumpfun-reconstruction/daybreak-disk-budget/`; it is not a canonical
repository input.

## Failure and recovery acceptance

Mocked measurements and tiny owned processes establish:

- initial low space rejects before source staging;
- post-staging low space rejects before compiler launch;
- runtime floor crossing stops the owned compiler/trial group and retains logs;
- an unrelated process remains alive;
- old binaries and receipts remain byte-identical or move through the existing
  output archive path;
- measurement failure is an infrastructure error, never experiment `fail`;
- resource failure retries in a fresh attempt after storage recovers;
- unchanged completed attempts resume only with a valid resource receipt;
- stale/tampered resource receipts are rejected even when their artifact hash
  is rewritten; and
- parent termination leaves an interrupted attempt whose resource evidence is
  retained and whose retry can complete.

## Tests

Targeted existing and new suites: **257 passed**, **13 explicitly skipped**,
**0 failed**.

- fastbuild: 57
- compiler process and ownership: 27
- experiments and recovery: 90
- bisection: 12
- minimization: 19
- provenance: 36
- paired build/source-boundary: 16

Project-required checks:

- `scripts/verify_evidence.py`: 9 captures verified
- `scripts/test_tooling.py`: 256 passed

The 13 skips require explicit SBF SDK/host compiler combinations or another
environment-specific prerequisite; no assertion failure was skipped.

## Reproduction

```bash
python3 reconstruction/harness/fastbuild.py \
  --src programs/pump \
  --work /tmp/pump-budget-work \
  --out /tmp/pump-budget-output \
  --recipe identity \
  --min-free-bytes 21474836480 \
  --disk-check-interval 1

python3 reconstruction/harness/resource_budget.py \
  /tmp/pump-budget-work/resource-receipts/attempt-*/resource-receipt.json

python3 -I -B reconstruction/harness/test_resource_budget.py
python3 -I -B reconstruction/harness/test_build_process_monitor.py
python3 -I -B reconstruction/harness/test_fastbuild_resource_budget.py
python3 -I -B reconstruction/harness/test_experiment_resource_budget.py
python3 -B reconstruction/harness/test_build_score_pair.py
```

## Limits

The guard measures rather than reserves storage. It cannot guarantee safety
against sudden external consumption, hostile detached processes, filesystem
failure or a whole-system crash. It does not infer APFS recoverability from
logical sizes and never deletes caches automatically. These results validate
the retained fixtures and one pinned build, not every host/filesystem.
