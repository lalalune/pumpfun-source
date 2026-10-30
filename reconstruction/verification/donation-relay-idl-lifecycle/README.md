# Donation Relay signed IDL lifecycle differential

This package executes Donation Relay's seven reserved Anchor IDL operations as
ordinary signed local transactions against two independent persistent LiteSVM
instances. One VM loads the retained deployed ELF; the other loads a separately
built candidate. It does not edit or import the frozen
`scripts/donation_relay_differential.py`.

The maintained `programs/donation-relay/src/idl.rs` is explicitly an uncompiled
application model. The executable path instead comes from Anchor 0.32's
generated `#[program]` dispatch. The captured ELF and the current candidate both
recognize selector `40f4bc78a7e9690a` and all seven authentic Borsh enum tags.
An invalid tag reaches the reserved dispatcher and returns Anchor 102.

## Covered executable contract

The primary persistent lifecycle performs:

1. canonical IDL account creation;
2. successful empty-account resize and rent transfer;
3. system-owned buffer allocation plus `CreateBuffer` initialization;
4. buffer write;
5. buffer copy into the canonical account;
6. rejection of resize after the account becomes nonempty;
7. authority transfer;
8. rejection of the former authority;
9. a write by the new authority;
10. close with exact rent transfer; and
11. repeated-close rejection.

Resize precedes the buffer copy because the executable contract rejects resize
when `data_len != 0` (Anchor 1002). The suite additionally covers absent and
readonly accounts, wrong owners, short and invalid headers, insufficient rent,
unauthorized signers, truncated and unknown operation payloads, a wrong Create
target, write capacity failure, and the 10,000-byte per-call resize cap. It also
records the important admitted behavior that a valid Relay-owned IDL-formatted
account need not have the canonical address for `Write`.

Each logical step is a separately signed transaction, except buffer allocation
and `CreateBuffer`, which are two genuine instructions atomically signed by the
fee payer, new buffer account, and authority. Signature and blockhash checking
are enabled. No signer bit is forged, no PDA signer is injected, and no RPC is
used.

The report retains exact transaction signatures, original/candidate errors,
logs, events, inner instructions, return data, compute consumption, and complete
watched before/after account state. Failed transactions must leave all non-fee
state unchanged. Executable image bytes are omitted from repeated account
snapshots but each ELF is independently SHA-256 bound.

## Build and replay

The build uses pinned platform-tools v1.44 and the locked dependency graph. The
ordinary candidate is a genuine SBF ELF, but is not claimed to reproduce PR
#2305's separately qualified Linux linker layout.

```sh
out=$(mktemp -d)
reconstruction/verification/donation-relay-idl-lifecycle/build_candidate.sh "$PWD" "$out"
uv run --python 3.12 --with solders==0.27.1 python \
  reconstruction/verification/donation-relay-idl-lifecycle/producer.py \
  --candidate "$out/donation_relay_candidate.so" \
  --output "$out/report-one.json"
uv run --python 3.12 --with solders==0.27.1 python \
  reconstruction/verification/donation-relay-idl-lifecycle/producer.py \
  --candidate "$out/donation_relay_candidate.so" \
  --output "$out/report-two.json"
cmp "$out/report-one.json" "$out/report-two.json"
uv run --python 3.12 --with solders==0.27.1 python \
  reconstruction/verification/donation-relay-idl-lifecycle/verify_report.py \
  --candidate "$out/donation_relay_candidate.so" --report "$out/report-one.json"
uv run --python 3.12 --with solders==0.27.1 python -m unittest \
  reconstruction/verification/donation-relay-idl-lifecycle/test_lifecycle.py
```

The output path must not exist; earlier receipts are never overwritten. Runtime
equality does not prove historical source completeness or ELF byte identity.
IDL operations emit no Anchor events, so event fields are compared and mutation
tested but there is no successful IDL event payload to claim. This package
credits the signed-pair and provenance pattern established by PR #2310 while
remaining separate from its donation and settlement cases.
