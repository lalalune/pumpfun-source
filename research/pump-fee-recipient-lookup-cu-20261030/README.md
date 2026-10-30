# Pump Main: fee-recipient admission cost per list slot, original vs rebuild

## Problem

Every legacy and v2 trade (`buy`, `buy_exact_sol_in`, `sell`, `buy_v2`,
`buy_exact_quote_in_v2`, `sell_v2`, plus `sweep_fees`) admits its
`fee_recipient` account through `validate_fee_recipient`
(`programs/pump/src/fee_recipient.rs`). The function has two lookups:

```
mayhem curve:  key == Global.reserved_fee_recipient || Global.reserved_fee_recipients.contains(&key)   (7 keys, linear)
               else NotAuthorized (6000)                                               fee_recipient.rs:19
normal curve:  key == Global.fee_recipient || Global.fee_recipients.binary_search(&key).is_ok()       (7 sorted keys)
               else NotAuthorized (6000)                                               fee_recipient.rs:35
```

Earlier Pump Main packets use one fixed recipient per case:
`pump-trade-post-fee-quote-boundaries` and `pump-v2-token-quote-fee-routing`
check whether a key is accepted. None of them measures what each slot costs,
and none checks whether the original and the rebuild compile the two lookups
to the same cost. This packet holds the trade fixed and moves only the
`fee_recipient` key. It reads the compute units (CU) on both images.

## Cases (60)

The 3 instructions are legacy `buy`, legacy `sell` and native-SOL `buy_v2`.
Each has two families:

- **normal (11 per instruction).** The curve is not in mayhem mode. The key is
  `Global.fee_recipient`, one of `fee_recipients[0..6]`, or one of 3 misses.
  The misses sort below all keys, between `[3]` and `[4]`, and above all keys.
- **mayhem (9 per instruction).** The curve has `is_mayhem_mode = 1`. The key
  is `Global.reserved_fee_recipient`, one of `reserved_fee_recipients[0..6]`,
  or `Global.fee_recipient`. The last one is a normal-family key, so it misses
  on a mayhem curve.

Each slot holds its own key, and keys are ordered by their first byte. The
fixture is otherwise the same in every case:

- Curve: vtr 1,073,000,000,000,000, vqr 30,000,000,000, rtr
  793,100,000,000,000, supply 10^15 and rqr 10^10.
- Trade: 10^9 tokens.
- Stub fees: 0/95/30 bps. Buyback 5,000 bps.

`buy_v2` derives `ata(fee_recipient, WSOL)` before validation, and the cost of
that derivation depends on the key's bump. To remove it as a confound, every
recipient key is chosen as the first `[first, second, j × 30]` whose WSOL ATA
has bump 255 (`canonical_key` in producer.py).

## Method

- `producer.py` is the post-fee trade harness of
  `research/pump-trade-post-fee-quote-boundaries-20261030` (via
  `pump-whitelist-mayhem-reserve-resync`). Only these parts were replaced: the
  recipient keys, the case plan, the summary (`cu_by_slot`) and the scope
  text.
- Pump runs under the upgradeable loader (program + programdata, the mainnet
  layout).
- The pump_fees slot holds a generated 9-instruction SBPFv0 stub. It returns
  the Fees bps through `sol_set_return_data`, and both images see the same
  stub.
- All accounts are synthetic, built from the IDL layouts. Keys come from fixed
  seeds. The clock is fixed. Each case runs in a fresh VM. There is no network.
- `runtime/plan.json.gz` holds every case's full initial state, metas and
  instruction bytes. `verify.py` replays from that file alone.
- Images:
  - original `evidence/original/pump/deployed.so`: sha256
    `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`,
    10,485,715 bytes.
  - rebuild `<candidate.so>`: sha256
    `ae713165a56752f7e1c6153137842e2b145885180b5c71e21a342afed45bd44b`,
    1,934,928 bytes. Built with `scripts/build_partial_candidate.py`
    (platform-tools v1.44 / cargo-build-sbf 2.1.21), source tree
    `9e5d2900ed30981d5766fb101ef120ee198161be`, repo commit
    `7e26cbf36c5c0c824e3eb36417ce8a35866f530a`.
  - fee stub (0/95/30) sha256
    `b2b7a41ffc54dafe89e42f1e1a7b320d4fadfd77c9274928e52393d9b7cc6c93`.

## Result

**Original and rebuild behave identically in all 60 cases**
(`behavior_mismatches = []`). The compared fields are: error, return data,
events, inner instructions, every non-executable account's after-state, and
whether the fee CPI was reached.

- There are 48 successes and 12 `NotAuthorized` (6000). Every miss fails on
  both images.
- In every success, the protocol fee goes to the key under test:
  - normal curve: 133 lamports, with the other 133 to the buyback recipient;
  - mayhem curve: the full 266 lamports, with no buyback split.
- CU is identical in 32 cases and logs are identical in 32 cases.

### CU per slot

Δ = CU minus the CU of the family's first row (the `Global` single-key slot),
on the original. The Δ column is the same on the rebuild in every row.

#### normal curve (`Global.fee_recipient`, then `binary_search` over 7 sorted keys)

| fee_recipient slot | stop | buy CU (orig / rebuild) | Δ | sell CU (orig / rebuild) | Δ | buy_v2 CU (orig / rebuild) | Δ |
|---|---|---|---|---|---|---|---|
| `global.fee_recipient` | success | 70,694 / 70,694 | +0 | 52,558 / 52,558 | +0 | 93,863 / 93,865 | +0 |
| `fee_recipients[0]` | success | 70,819 / 70,819 | +125 | 52,683 / 52,683 | +125 | 93,988 / 93,990 | +125 |
| `fee_recipients[1]` | success | 70,775 / 70,775 | +81 | 52,639 / 52,639 | +81 | 93,944 / 93,946 | +81 |
| `fee_recipients[2]` | success | 70,818 / 70,818 | +124 | 52,682 / 52,682 | +124 | 93,987 / 93,989 | +124 |
| `fee_recipients[3]` | success | 70,731 / 70,731 | +37 | 52,595 / 52,595 | +37 | 93,900 / 93,902 | +37 |
| `fee_recipients[4]` | success | 70,818 / 70,818 | +124 | 52,682 / 52,682 | +124 | 93,987 / 93,989 | +124 |
| `fee_recipients[5]` | success | 70,774 / 70,774 | +80 | 52,638 / 52,638 | +80 | 93,943 / 93,945 | +80 |
| `fee_recipients[6]` | success | 70,817 / 70,817 | +123 | 52,681 / 52,681 | +123 | 93,986 / 93,988 | +123 |
| `miss-below-all` | NotAuthorized | 35,732 / 35,718 | — | 25,986 / 25,972 | — | 59,411 / 59,397 | — |
| `miss-between-3-and-4` | NotAuthorized | 35,731 / 35,717 | — | 25,985 / 25,971 | — | 59,410 / 59,396 | — |
| `miss-above-all` | NotAuthorized | 35,729 / 35,715 | — | 25,983 / 25,969 | — | 59,408 / 59,394 | — |

#### mayhem curve (`Global.reserved_fee_recipient`, then linear `contains` over 7 keys)

| fee_recipient slot | stop | buy CU (orig / rebuild) | Δ | sell CU (orig / rebuild) | Δ | buy_v2 CU (orig / rebuild) | Δ |
|---|---|---|---|---|---|---|---|
| `global.reserved_fee_recipient` | success | 68,438 / 68,438 | +0 | 52,194 / 52,194 | +0 | 91,621 / 91,623 | +0 |
| `reserved_fee_recipients[0]` | success | 68,465 / 68,465 | +27 | 52,221 / 52,221 | +27 | 91,648 / 91,650 | +27 |
| `reserved_fee_recipients[1]` | success | 68,492 / 68,492 | +54 | 52,248 / 52,248 | +54 | 91,675 / 91,677 | +54 |
| `reserved_fee_recipients[2]` | success | 68,519 / 68,519 | +81 | 52,275 / 52,275 | +81 | 91,702 / 91,704 | +81 |
| `reserved_fee_recipients[3]` | success | 68,546 / 68,546 | +108 | 52,302 / 52,302 | +108 | 91,729 / 91,731 | +108 |
| `reserved_fee_recipients[4]` | success | 68,573 / 68,573 | +135 | 52,329 / 52,329 | +135 | 91,756 / 91,758 | +135 |
| `reserved_fee_recipients[5]` | success | 68,600 / 68,600 | +162 | 52,356 / 52,356 | +162 | 91,783 / 91,785 | +162 |
| `reserved_fee_recipients[6]` | success | 68,627 / 68,627 | +189 | 52,383 / 52,383 | +189 | 91,810 / 91,812 | +189 |
| `fee_recipient-on-mayhem-curve` | NotAuthorized | 35,786 / 35,772 | — | 26,040 / 26,026 | — | 59,465 / 59,451 | — |

Reading the tables (measured values only):

- **The mayhem lookup is linear.** Slot `[i]` costs exactly 27·(i + 1) CU more
  than the `Global.reserved_fee_recipient` slot. This holds on all 3
  instructions and on both images.
- **The normal lookup follows binary-search depth.** Slot `[3]` (the midpoint
  of 7) costs +37 CU. Slots `[1]` and `[5]` cost +80/+81. Slots `[0]`, `[2]`,
  `[4]` and `[6]` cost +123..+125. Again this holds on all 3 instructions and
  both images. `fee_recipients[0]` is the most expensive slot, not the
  cheapest.
- The three normal misses differ from each other by at most 3 CU on each
  image.
- **The lookup costs the same on both images.** Within each (instruction,
  family) block, orig − rebuild is constant across all slots.

### Compute-unit / log differences

| orig − rebuild | cases | where | differing log lines |
|---|---|---|---|
| +14 | 12 | every `NotAuthorized`: `fee_recipient.rs:35` (normal-curve miss, 9) and `fee_recipient.rs:19` (mayhem-curve miss, 3) | AnchorError site `programs/pump/src/fee_recipient.rs:N` (original) vs `src/fee_recipient.rs:N` (rebuild), plus `consumed` |
| −2 | 16 | every `buy_v2` success, both families, every slot | `consumed` only |
| 0 | 32 | every legacy `buy` / `sell` success | none |

Cause locations:

- **+14.** This equals `len("programs/pump/")`, the extra characters in the
  original's AnchorError file string that the `err!` log formats. It is the
  same signature recorded for the other `require!`/`err!` sites in earlier Pump
  Main packets.
- **−2.** This is constant across all 16 `buy_v2` successes and does not move
  with the slot, so it is not in `validate_fee_recipient`. It is the same −2
  that `pump-trade-post-fee-quote-boundaries` and
  `pump-whitelist-mayhem-reserve-resync` record for fee-charging `buy_v2`. This
  packet does not determine its instruction-level location.

## Limits

- Covers 3 of the 7 call sites: `buy`, `sell` and `buy_v2`.
  `buy_exact_sol_in`, `buy_exact_quote_in_v2`, `sell_v2` and `sweep_fees` call
  the same function, but they are not run here.
- Native-SOL quote only. One loader (upgradeable). Synthetic state.
- Every key differs from its neighbours in the first byte. Keys that share a
  long prefix (where a 32-byte compare runs longer) are not measured.
- Unsorted `fee_recipients` are not measured, because the setter rejects them
  (`UnsortedNotUniqueFeeRecipients`).

## Reproduce

```
python3 producer.py --root <repo> --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}' --out .
python3 verify.py --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}'
```

The producer output is byte-identical across runs. verify.py first checks both
image sha256 values against `runtime/report.json.gz`. It then replays all 60
cases × 2 images (120 receipts) and compares each receipt byte for byte. Last,
it recomputes the summary, including `cu_by_slot`, which the tables above are
read from. It exits 0 on success and 1 on any difference.

Files: `producer.py`, `verify.py`, `runtime/plan.json.gz`,
`runtime/receipts-upgradeable.jsonl.gz` and `runtime/report.json.gz`
(summary, `cu_by_slot`, per-case rows with lamport deltas and TradeEvents).
