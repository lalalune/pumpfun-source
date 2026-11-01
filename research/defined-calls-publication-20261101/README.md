# Publish complete defined-call diagnostic packets

On base `60a42309a4908577f0a386513eeaee6cd6f84f42`, the maintained
`reconstruction/diagnostics/defined-dynamic-calls/generate.py` writes into its
final destination before appending attribution and the manifest. A real POSIX
64-byte file-size limit leaves a truncated `pump-details.json`, no manifest and
an occupied destination that prevents a normal retry. A dangling output link
also resolves to, creates and populates its otherwise absent target.

Stage the complete packet beside the lexical output path, then use the existing
native no-replace publication helper. Ordinary exceptions remove the private
stage. Existing outputs, dangling leaf links and a late destination are
preserved; parent-directory aliases remain supported. This follows
[#3002](https://github.com/lalalune/pumpfun-source/pull/3002) and
[#3006](https://github.com/lalalune/pumpfun-source/pull/3006), whose accepted scope
explicitly left this sibling for follow-up. Reusing the maintained helper also
retains its bounded staging names and caller umask, without another rename
implementation or changes to the archived roadmap.

## Reproduce

Run from the repository with Python and the repository's pyelftools dependency:

```sh
python -B research/defined-calls-publication-20261101/probe.py --repo . \
  --revision 60a42309a4908577f0a386513eeaee6cd6f84f42 --expect base --output /tmp/defined-before.json
python -B research/defined-calls-publication-20261101/probe.py --repo . \
  --expect fixed --output /tmp/defined-after.json
python -B reconstruction/diagnostics/defined-dynamic-calls/test_generate.py
python -B scripts/test_tooling.py
python -B scripts/verify_evidence.py
```

The same probe copies exact selected source files and all three retained captures
into an owned temporary cohort. It invokes the real CLI ten times per revision
and validates every successful emitted manifest and standalone verifier. It
never changes caller inputs or invokes a compiler, program or VM.

| Case | Base | Fixed |
| --- | --- | --- |
| 64-byte file-size limit | Partial final directory | Final directory absent, stage removed |
| Unlimited retry at same path | Refused | Complete verified packet |
| Dangling output link | Target created and populated | Refused, link retained and target absent |
| Normal, 240-byte ASCII name, 240-byte Korean name, parent alias | Verified | Verified, same packet |
| Existing empty/populated destination | Refused and preserved | Refused and preserved |
| Destination created after roadmap returns | Observer cannot claim already-written output | Refused; observer-created empty directory retained |

The late-writer observer watches the actual `generate_roadmap` return and creates
only an absent owned output; it neither replaces the generator nor changes its
result. This is a fixed-version no-replace control, not evidence that the old
version overwrites a concurrent destination.

All seven original roadmap payloads are byte-identical across revisions. Only
`dynamic-call-inputs.json` and its manifest hash change; attribution content is
identical except for the adapter's own SHA256. All selected source bytes other
than this adapter, all captures, and historical packets remain unchanged. The
proof records the source identity of the shared publication helper; it does not
claim that the adapter transitively pins every imported module.

Five focused methods, 255 required tooling tests and nine capture checks passed
on macOS arm64 / CPython 3.12.13. Existing CI already invokes the modified test
module. The unchanged required tooling suite includes its existing runtime
fixtures; the new proof is static. No call classification, matching score,
program source, archived packet or captured binary changes. Publication is
qualified for supported native no-replace hosts under ordinary exceptions, not
power-loss durability, all operating systems or cleanup after an uncatchable
process kill.
