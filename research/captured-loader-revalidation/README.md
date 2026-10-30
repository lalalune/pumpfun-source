# Revalidate the saved captured-loader evidence

The parallel differential runner's `--validate-existing --captured-loader` path
checks the profile name and suite results but never reads the saved loader
receipts. It also publishes an empty `loader_receipts` mapping. Removing a real
receipt can therefore still yield a successful new captured-upgradeable report.

Use the same receipt admission for executed and saved suites: exact fixture and
loader/capture input hashes, original/candidate ELF identities and existing
account-layout checks. Saved reports must retain exactly one entry per selected
suite, with the same path, hash and load count. Bind admitted receipt bytes until
final publication and carry the entries into the revalidated report. Legacy-raw
reports retain their existing mode.

The proof uses the actual verified builder with the authenticated official native
v1.44 SDK and the admitted Linux v1.44 SBPF library profile. It then executes the
complete supported shard 4/4: 11 suites and 2605 original/candidate differential
cases through the captured upgradeable loader. It revalidates that genuine report,
checks the unchanged complete case payload and loader entries, preserves then
temporarily moves a real receipt, and separately changes its bytes. Both negative
requests must reject before publishing a success report. No authoritative report,
ELF, compiler result, VM outcome or loader receipt is synthesized.

Run on a provisioned native macOS ARM host with the pinned Python dependencies:

```sh
python -B research/captured-loader-revalidation/reproduce.py
```

`work/scoped-proof` retains the actual candidate/unstripped ELF gzip files, producer
build record/log, execution report, loader receipts, all suite outputs/logs and
the three validation process logs. Generated SDK/target/dependency directories
are outside that upload. This is bounded evidence admission and preservation,
not whole-program equivalence, live-chain execution or a security assessment.

The adjacent proposed asset transition records the exact old/new SHA-256 of the
single edited root script. Historical sealed manifests and original captures are
preserved; this packet proposes the reviewed script transition only.
