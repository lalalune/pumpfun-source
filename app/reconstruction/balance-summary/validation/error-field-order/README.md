# Original error-field order correction

Independent static review found that each of the six captured error classes
declares `status; retryAfterMs;` before its constructor assigns `name`. The first
maintained version assigned these properties only in the constructor, preserving
consumed values but changing enumerable own-property order. This correction
restores the two original class fields and adds the observable order assertion
to the existing error-path case. It changes no HTTP/query/JSON policy.

Frozen corrected source: `d293c3b4187e8530095a3d245a4c2ea229ab6827`, tree
`a416e1214467543ff73f8ca5fc1db313d88be78d`. The source diff from local
`5c5278944ae5d20c99cb3df9a67491db5a759132` is only those two declarations and
the own-key assertion. Public original source `dcf02e875c71df8cddbe3954294eb6205b9a86ad`
and first packet head `81095133bcb4e03bd821fdf45221d0afc2676ba1` remain preserved
in branch history. The parent packet's files/manifests are unchanged.

On the corrected source, all nine affected tests, the source verifier, and the
required nine root captures/ten tooling tests pass. The common check's 46 actual
read inputs match corrected-source Git blobs. The loopback fixture is run fresh:
seven complete synthetic GET responses and one actual aborted GET. Its normalized
wire receipt is byte-identical to the initial one. Shared-source, app698/progress
checks remain historical initial results; they were not rerun or transferred as
fresh final-source runs.

`own-property-observation.json` records the same native construction of the old
and corrected **maintained** classes. Before keys are name/status/retryAfterMs;
after they are status/retryAfterMs/name, as defined by the original class-field
syntax. Name/status/delay values are unchanged. Original captured factories are
never executed. The actual UI caller uses error truthiness and finite status,
not enumeration; no observed UI failure or accounting fix is claimed.

Reproduce the affected checks from repository root:

```sh
node app/scripts/original-balance-summary.mjs --check
node --test app/tests/original_balance_summary.test.mjs
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
```

No Next/browser/live service/auth/credential/RPC/mutation or original-backend
qualification is involved. `VALIDATION.json` records actual source hashes and
commands; the parent packet retains all earlier measurements honestly.
