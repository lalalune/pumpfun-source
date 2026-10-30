# Donation Relay signed stateful differential

This package replaces the non-runnable input assumptions in
`scripts/donation_relay_differential.py` with paths that exist on current main.
It never modifies that frozen script or captured evidence. It loads the retained
Relay, SPL Token and Associated Token ELFs, and it requires a separately built
candidate ELF.

## Honest coverage boundary

The original program hard-codes the production relayer
`RLYRf96HAJSbbXCNS6ibQYnkxtb6kbfuFxqEkm9oQUc`. The repository retains that
public key but no corresponding private key or independently reproducible key
derivation. LiteSVM signature verification is enabled, all submitted signatures
come from deterministic test-owned keypairs, and this package does not inject a
signer bit. Consequently, successful whitelist update, epoch close,
distribution, next-epoch admission, and Jupiter paths are **unsupported
fixtures**, not matches. The signed authority rejection and rollback paths do
execute against both images.

Supported execution consists of eleven fresh stateful cases / fourteen signed
transactions:

- two donations in separate transactions to the same epoch;
- zero donation;
- message, tip, balance, PDA, token-mint, and account-owner rejection;
- a successful donation followed by a failing donation, with rollback checked;
- whitelist-update and close-epoch attempts signed by a real, controlled but
  non-production authority, with rollback checked.

Every step compares the exact error, relevant logs, event log records, inner
instructions, return data, verified transaction signature, lamports, owners,
data lengths, data hashes and complete bytes of watched accounts. Compute-unit
lines and counts are retained for evidence but do not determine semantic
equality. A changed expected debouncer total is a negative control and must be
detected. The final report also requires every logical step to have a verified,
unique transaction signature.

## Build and run

The build uses the repository's pinned macOS arm64 platform-tools v1.44 and the
locked dependency graph. Populate the Cargo cache once with `cargo fetch
--locked`; the build itself is offline.

```sh
out=$(mktemp -d)
reconstruction/verification/donation-relay-stateful/build_candidate.sh "$PWD" "$out"
python3 reconstruction/verification/donation-relay-stateful/producer.py \
  --candidate "$out/donation_relay_candidate.so" \
  --output "$out/report.json"
python3 -m unittest \
  reconstruction/verification/donation-relay-stateful/test_stateful.py
```

The ordinary build is a genuine SBF candidate, but it does not apply the
historical exact-linker-layout packet removed from current main. Therefore this
package makes runtime-behavior claims only; it does not claim this locally built
file has the selected Relay's exact byte layout.

The JSON report pins the original, candidate, dependency, and complete
maintained Relay source hashes. It uses four explicit classifications:
`equal_observed_behavior`, `different_behavior`, `unsupported_fixture`, and a
fatal infrastructure error. Unsupported cases never contribute to the match
count.
