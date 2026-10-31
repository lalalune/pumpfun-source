# Bind saved Mayhem trade snapshots to declared images

Base: `ca03a2b41cab9fa839e39a91d9e18046d9660c08`.
Five saved-receipt verifiers cover six trade selectors: buy, sell, buy_v2,
sell_v2 and both PumpSwap directions. Their headers are checked against the
selected original/candidate files, but executable snapshots are excluded from
account-data hashing and Mayhem's program account is excluded from pair parity.
Consequently, the declared candidate can differ from the image recorded in
the retained runtime snapshots.

Require each original/candidate Mayhem snapshot, before and after execution,
to exist, be marked with JSON boolean `executable: true`, and carry the SHA-256
of that side's already authenticated ELF. Existing signature, selector,
rollback, error, state, CPI, event and output-admission checks stay intact.
The runtime producer and its loader are unchanged. These producers use the
legacy LiteSVM loader and record the loaded ELF's complete data digest.

This is internal consistency validation of saved evidence. It does not
cryptographically attest that arbitrary external JSON really came from a VM.
The five current-script hash transitions are proposed alongside this packet;
historical captures, packages, receipts and script copies remain unchanged.

## Genuine runtime proof

On a LiteSVM-capable host with Python 3.12 and pinned `requirements.txt`:

```sh
python -B research/mayhem-trade-image-binding/reproduce.py
python -B scripts/test_mayhem_receipt_admission.py
python -B scripts/verify_evidence.py
python -B scripts/test_tooling.py
```

The identical reproduction is run on the proof-only base and the change.
It uses the existing `execute_rejection` helper for 12 actual independent
LiteSVM executions across six short-payload trade selectors. Test-owned
payers sign normally; sigverify and blockhash checks are enabled. No VM
account, result, signature or positive receipt is mocked.

Six untouched captured-Mayhem controls must be accepted. Explicitly marked
negative copies then contradict those genuine snapshots: relabel a header
with the actual Fees ELF's digest and select that ELF on the verifier CLI;
change each side/phase snapshot digest; or use an integer executable marker.
These negative copies are never presented as actual Fees VM execution or
positive verification evidence. Transactions and the fixture producer stay
unchanged. Some per-phase negatives may already fail the old rollback checks;
only measured before results establish which contradictions were admitted.

All 42 verifier CLI outcomes, input receipts, output reports and logs are
retained before final assertions under `work/scoped-proof`, including bad
base outputs. Runtime helper AST, native solders module, captures and verifier
hashes bind the proof. The fixed result must accept all six genuine controls
and reject all 36 marked negatives without publishing a success report.

## Scope and limits

This is one saved-verifier-family fix, not separate tasks per selector. The
controls prove signed rejection receipt admission, not successful trade-path
coverage, fresh source compilation, rebuilt-program equivalence, whole-ELF
identity or a security finding. No source, binary, signer/owner policy or
stopped research lane is changed. Earlier #2541 concerns runtime producer
pinning; #3243 concerns a separate burn-receipt format. Neither is modified.
