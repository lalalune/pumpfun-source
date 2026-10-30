# Pump Main creator-fee collection: destination boundaries and in-transaction sequences

## Problem

`collect_creator_fee` (v1) and `collect_creator_fee_v2` pay the creator vault PDA
(`["creator-vault", creator]`) out to `creator`. On the native path the amount is
`vault.lamports - rent_minimum(0)` and the payout is a System transfer signed by
the vault seeds. On the v2 SPL-quote path the amount is the vault ATA's token
balance. Before paying, the handler checks, in this order:

1. `creator.owner == pump_fees` -> error 6050 `UnableToDistributeCreatorVaultMigratedToSharingConfig`
2. `creator.executable` -> success, log `Creator account is executable, so it cannot receive lamports`
3. `amount == 0` -> success, log `No creator fee to collect`
4. native only: `creator.lamports + amount < rent(creator.data_len)` -> success,
   log `Creator account does not have enough rent-exemption lamports`

The repository harnesses (`scripts/pump_creator_collect_differential.py`,
`scripts/pump_creator_collect_v2_differential.py`) vary the vault balance and the
account metas. In those harnesses the creator is always a funded, data-less,
system-owned wallet. No harness looks at the destination side: an absent or
under-funded creator, a creator that holds data, foreign owners, the pump_fees
owner, lamport overflow. No harness chains collections with deposits, rent
top-ups or a later failing instruction in the same transaction either. This
packet runs those cases on the original image and on the rebuild and compares
them.

## Setup

- Images: original `evidence/original/pump/deployed.so`
  (sha256 `7a19affa…f7b02d`) and rebuild `candidate.so`
  (sha256 `1cbf63ae…ab81c6`). Both use the upgradeable loader layout
  (program account + programdata).
- Only the Pump program is loaded. System, SPL Token and the ATA program are
  LiteSVM built-ins. pump_fees is never invoked; its id only appears as an
  account owner.
- All state is synthetic. The fee payer comes from a fixed seed, and the clock is
  fixed per case (`unix_timestamp` 1,800,000,000, or -1 in one case pair). Each
  case starts from its own account set. `rent_minimum(0)` = 890,880 lamports and
  `rent(165)` = 2,039,280 lamports.
- The v2 native path uses `quote_mint` = WSOL. The v2 SPL path uses a 6-decimal
  SPL Token mint, with an existing creator ATA unless the case says otherwise.

## Cases

There are 66 cases, giving 132 receipts (2 images x 66). Where a case has a `v1-`
and a `v2-` form, both forms take the same state.

- Destination boundaries (18 v1/v2 pairs):
  - absent creator with surplus rent(0)-1, rent(0) and 1;
  - creator holding 1 lamport with `1 + amount` = rent(0) and rent(0)-1;
  - system-owned creator with 165 data bytes, short of rent(165) by 1 and exact;
  - creator owned by SPL Token, owned by Pump, and owned by pump_fees (with a
    funded vault, an exactly-rent vault and an absent vault);
  - executable creator (the ATA program id);
  - creator at `u64::MAX - 10` lamports receiving 10 and 11;
  - a vault holding 2^62 lamports, a Pump-owned vault, and a vault with 1 data byte.
- Creator = the transaction fee payer, and a negative clock timestamp
  (2 pairs).
- Sequences in one transaction (8 v1/v2 pairs + 2 mixed):
  - collect twice;
  - collect, deposit 5,000, collect;
  - vault at exactly rent(0), deposit 1, collect;
  - absent creator, collect, payer tops the creator up by 390,880 (and by
    390,879), collect;
  - two creators;
  - collect followed by a failing System transfer;
  - v1 then v2, and v2 then v1, with a 7,000 deposit in between.
- v2 SPL-quote path (8 cases): vault ATA balance 1 / `u64::MAX` / 0; collect
  twice; missing creator ATA; frozen vault ATA; SPL collect then native collect;
  creator owned by pump_fees.

## Result

**Behavior: original and rebuild match in all 66 cases.** In every case these
are identical on both images: the transaction bytes, the error, the handler
messages, the `Program data` events, the inner instructions (including the
`emit_cpi` self-invocation), and every account's lamports, owner and data hash
after the transaction.

**Logs and compute units: 59 of 66 cases are identical.** The 7 cases that
differ are exactly the error-6050 cases (pump_fees-owned creator: 3 v1, 3 v2
native, 1 v2 SPL). In each one only two log lines differ:

- the AnchorError site reads `programs/pump/src/creator/collect_creator_fee.rs:103`
  (v1) or `:198` (v2) on the original, and `src/creator/collect_creator_fee.rs:103`
  / `:198` on the rebuild;
- the original consumes 14 CU more (v1 6,871 vs 6,857; v2 native 11,978 vs 11,964;
  v2 SPL 17,978 vs 17,964).

Only the logged source path, and the compute it takes to log it, differs. This
is not a behavior difference.

Measured behavior (identical on both images):

| Case group | Outcome | Creator lamport change |
|---|---|---|
| absent creator, surplus rent(0)-1 or 1 | success, "not enough rent-exemption", no transfer | 0 |
| absent creator, surplus = rent(0) | transferred, 1 event | +890,880 |
| creator 1 lamport, surplus rent(0)-1 / rent(0)-2 | transferred / skipped | +890,879 / 0 |
| 165-byte creator, short by 1 / exact | skipped / transferred | 0 / +1,000 |
| creator owned by SPL Token or Pump | transferred (System credits a non-system account) | +1,000,000 |
| creator owned by pump_fees, vault funded / rent-only / absent | error 6050 in all three; the owner check comes before the vault is read | 0 |
| executable creator | success, "executable" message, no transfer | 0 |
| creator at u64::MAX-10, +10 / +11 | transferred / `ArithmeticOverflow` from the System transfer | +10 / 0 |
| vault 2^62 lamports | transferred | +4,611,686,018,426,497,024 |
| Pump-owned vault / vault with 1 data byte | `ExternalAccountLamportSpend` / `InvalidArgument` from the System transfer | 0 |
| creator = fee payer, surplus 123,456 | transferred | +118,456 (net of the transaction fee) |
| negative `unix_timestamp` | transferred, 1 event | +777 |

Sequences (identical on both images):

- collect, collect: 1 event, +50,000. The second collect logs "No creator fee to collect".
- collect, deposit 5,000, collect: 2 events, +55,000.
- vault exactly rent(0), deposit 1, collect: the first collect logs "No creator
  fee"; the second transfers 1 (1 event, +1).
- absent creator, surplus 500,000:
  - The first collect is skipped ("not enough rent-exemption").
  - After a 390,880 top-up, the second collect transfers 500,000: 1 event,
    creator +890,880.
  - With a 390,879 top-up, both collects are skipped: 0 events, creator +390,879.
- two creators: 2 events.
- collect then a failing System transfer (`Custom(1)` at instruction 1): the
  collect's event line is logged, but the transaction is rolled back and the
  creator change is 0.
- v1 then v2, and v2 then v1, around a 7,000 deposit: 2 events, +47,000, and
  31,744 CU for both orders.
- v2 SPL:
  - Balances 1 and `u64::MAX` are transferred (1 event each).
  - Balance 0 logs "No creator fee". The 99 lamports of vault surplus are not
    collected on the SPL path.
  - A missing creator ATA fails in SPL Token with `InvalidAccountData`.
  - A frozen vault ATA fails with `Custom(17)`.
  - SPL collect then native collect: 2 events, creator +99 lamports.

## Files

- `producer.py`: builds the plan, runs both images and writes `runtime/`.
- `verify.py`: replays `runtime/plan.json.gz` on both images and compares each
  receipt and the summary byte for byte. It imports the execution code from
  `producer.py` in this folder and reads no repository files.
- `runtime/plan.json.gz`: every case's initial accounts and instruction list.
- `runtime/receipts-upgradeable.jsonl.gz`: 132 receipts (tx, error, logs, CU,
  events, handler messages, inner instructions, account after-state).
- `runtime/report.json.gz`: image sha256s, per-case comparison, and summary counts.

## Reproduce

```
python3 producer.py --root <repo> \
  --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}' \
  --out .
python3 verify.py --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}'
```

The producer is deterministic: two runs give byte-identical `runtime/` files.
It needs solders 0.27.1 (`solders.litesvm`) and no network.
