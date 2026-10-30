# Pump Main: buyback-fee-recipient admission cost per list slot, original vs rebuild

## Problem

Six handlers admit the buyback fee recipient through
`Global::validate_buyback_fee_recipient` (`programs/pump/src/lib.rs`):

- legacy `buy`, `buy_exact_sol_in` and `sell`, where the recipient is
  `remaining_accounts[1]`;
- native-SOL `buy_v2`, `buy_exact_quote_in_v2` and `sell_v2`, where it is the
  named `buyback_fee_recipient` account.

The function runs two checks:

```
require_keys_neq!(key, Pubkey::default(), BuybackFeeRecipientMissing)            lib.rs:1879  (6062)
require!(Global.buyback_fee_recipients.contains(&key), BuybackFeeRecipientNotAuthorized)   lib.rs:1884  (6057; 8 keys, linear)
```

Earlier packets have measured this function only on `buy_v3`
(`pump-v3-trade-boundaries`, case `buy/buyback-default`) and with one fixed
buyback key per case. They did not measure the per-slot cost or the six
legacy/v2 call sites. This packet holds the trade fixed and moves only the
buyback key. It reads the compute units (CU) on both images.

## Cases (60)

There are 6 instructions × 10 keys. The keys are:

- `buyback_fee_recipients[0..7]` (8);
- a key not in the list;
- `Pubkey::default()`.

The fixture is the same in every case:

- Curve: not in mayhem mode, vtr 1,073,000,000,000,000, vqr 30,000,000,000,
  rtr 793,100,000,000,000, supply 10^15 and rqr 10^10.
- Fee recipient: `Global.fee_recipient`.
- Stub fees: 0/95/30 bps. `buyback_basis_points`: 5,000.
- Trades: `buy`/`buy_v2` buy 10^9 tokens (max cost 10^15). `buy_exact_sol_in`/
  `buy_exact_quote_in_v2` spend 10^9 lamports (min out 1). `sell`/`sell_v2`
  sell 10^9 tokens.

The v2 handlers derive `ata(buyback_fee_recipient, WSOL)`, and that
derivation's cost depends on the key's bump. To remove it as a confound, the 9
non-default keys are each chosen as the first `[first, 0, j × 30]` whose WSOL
ATA has bump 255 (`canonical_key` in producer.py).

## Method

- `producer.py` is the post-fee trade harness of
  `research/pump-trade-post-fee-quote-boundaries-20261030` (via
  `pump-whitelist-mayhem-reserve-resync`). Only these parts were replaced: the
  buyback keys, the case plan, the summary (`cu_by_slot`) and the scope text.
- Pump runs under the upgradeable loader (program + programdata, the mainnet
  layout).
- The pump_fees slot holds a generated 9-instruction SBPFv0 stub that returns
  the Fees bps through `sol_set_return_data`. Both images see the same stub.
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

- There are 48 successes, 6 `BuybackFeeRecipientNotAuthorized` (6057, the key
  not in the list) and 6 `BuybackFeeRecipientMissing` (6062, the
  default key), on both images.
- In every success, the buyback half of the protocol fee goes to the key under
  test, whatever its slot:
  - `buy`, `sell`, `buy_v2`, `sell_v2`: fee 266, of which 133 goes to the
    buyback key and 133 to the fee recipient;
  - `buy_exact_sol_in`, `buy_exact_quote_in_v2`: fee 9,382,717, of which
    4,691,358 goes to the buyback key and 4,691,359 to the fee recipient.
- CU is identical in 24 cases and logs are identical in 24 cases.

### CU per slot

Δ = CU minus the `buyback_fee_recipients[0]` row of the same instruction, on
the original. The Δ is the same on the rebuild in every success row.

| buyback slot | stop | buy CU orig / rebuild (Δ) | buy_exact_sol_in CU orig / rebuild (Δ) | sell CU orig / rebuild (Δ) | buy_v2 CU orig / rebuild (Δ) | buy_exact_quote_in_v2 CU orig / rebuild (Δ) | sell_v2 CU orig / rebuild (Δ) |
|---|---|---|---|---|---|---|---|
| `buyback_fee_recipients[0]` | success | 70,694 / 70,694 (+0) | 72,014 / 72,014 (+0) | 52,558 / 52,558 (+0) | 95,363 / 95,365 (+0) | 96,797 / 96,799 (+0) | 84,341 / 84,344 (+0) |
| `buyback_fee_recipients[1]` | success | 70,720 / 70,720 (+26) | 72,040 / 72,040 (+26) | 52,584 / 52,584 (+26) | 95,389 / 95,391 (+26) | 96,823 / 96,825 (+26) | 84,367 / 84,370 (+26) |
| `buyback_fee_recipients[2]` | success | 70,746 / 70,746 (+52) | 72,066 / 72,066 (+52) | 52,610 / 52,610 (+52) | 95,415 / 95,417 (+52) | 96,849 / 96,851 (+52) | 84,393 / 84,396 (+52) |
| `buyback_fee_recipients[3]` | success | 70,772 / 70,772 (+78) | 72,092 / 72,092 (+78) | 52,636 / 52,636 (+78) | 95,441 / 95,443 (+78) | 96,875 / 96,877 (+78) | 84,419 / 84,422 (+78) |
| `buyback_fee_recipients[4]` | success | 70,798 / 70,798 (+104) | 72,118 / 72,118 (+104) | 52,662 / 52,662 (+104) | 95,467 / 95,469 (+104) | 96,901 / 96,903 (+104) | 84,445 / 84,448 (+104) |
| `buyback_fee_recipients[5]` | success | 70,824 / 70,824 (+130) | 72,144 / 72,144 (+130) | 52,688 / 52,688 (+130) | 95,493 / 95,495 (+130) | 96,927 / 96,929 (+130) | 84,471 / 84,474 (+130) |
| `buyback_fee_recipients[6]` | success | 70,850 / 70,850 (+156) | 72,170 / 72,170 (+156) | 52,714 / 52,714 (+156) | 95,519 / 95,521 (+156) | 96,953 / 96,955 (+156) | 84,497 / 84,500 (+156) |
| `buyback_fee_recipients[7]` | success | 70,876 / 70,876 (+182) | 72,196 / 72,196 (+182) | 52,740 / 52,740 (+182) | 95,545 / 95,547 (+182) | 96,979 / 96,981 (+182) | 84,523 / 84,526 (+182) |
| `miss-not-in-list` | BuybackFeeRecipientNotAuthorized | 35,884 / 35,870 | 35,888 / 35,874 | 43,445 / 43,431 | 61,043 / 61,029 | 61,043 / 61,029 | 58,282 / 58,268 |
| `default-pubkey` | BuybackFeeRecipientMissing | 35,959 / 35,841 | 35,963 / 35,845 | 43,520 / 43,402 | 62,617 / 62,499 | 62,617 / 62,499 | 59,856 / 59,738 |

Reading the table (measured values only):

- **The lookup is linear.** Slot `[i]` costs exactly 26·i CU more than slot
  `[0]`. This holds on all 6 instructions and on both images.
- **The lookup itself costs the same on both images.** Within each
  instruction, orig − rebuild is constant across the 8 success rows: 0 for
  legacy, −2 for `buy_v2` and `buy_exact_quote_in_v2`, −3 for `sell_v2`.
- **The two failure rows rank differently on the two images.** Take the legacy
  `buy`:
  - original: the default-key failure costs 75 CU *more* than the not-in-list
    failure (35,959 vs 35,884);
  - rebuild: it costs 29 CU *less* (35,841 vs 35,870).
  The default key is checked first (lib.rs:1879), before the 8-key scan. Its
  error also logs four extra lines on both images: `Left:`, a pubkey, `Right:`
  and a pubkey.

### Compute-unit / log differences

| orig − rebuild | cases | where | differing log lines |
|---|---|---|---|
| +118 | 6 | every `BuybackFeeRecipientMissing` (`require_keys_neq!`, `lib.rs:1879`), all 6 instructions | AnchorError site `programs/pump/src/lib.rs:1879` vs `src/lib.rs:1879`, plus `consumed`. The `Left:`/`Right:` pubkey lines are identical |
| +14 | 6 | every `BuybackFeeRecipientNotAuthorized` (`require!`, `lib.rs:1884`), all 6 instructions | AnchorError site path, plus `consumed` |
| −2 | 16 | every `buy_v2` / `buy_exact_quote_in_v2` success, independent of slot | `consumed` only |
| −3 | 8 | every `sell_v2` success, independent of slot | `consumed` only |
| 0 | 24 | every legacy success | none |

Cause locations:

- **+14.** This equals `len("programs/pump/")` in the AnchorError file string.
- **+118 = 14 + 104.**
  - The 14 is the same site string. The other 104 CU are not explained by any
    log line: every other log line is identical, including both pubkey lines.
  - The extra cost appears only on the `require_keys_neq!` site (`:1879`). The
    `require!` site 5 lines later (`:1884`) shows only +14.
  - The same +118 is recorded for `lib.rs:1879` on `buy_v3` in
    `pump-v3-trade-boundaries-20261030`. A +14 / 104 CU split is recorded for
    other single-site errors in `pump-trade-post-fee-quote-boundaries-20261030`.
  - This packet narrows the 104 to the `require_keys_neq!` error path of this
    one function. It does not locate the instructions.
- **−2 / −3.** These are constant across all slots, so they are not in
  `validate_buyback_fee_recipient`. They match the −2 (buy_v2) and −3
  (sell_v2) recorded for fee-charging v2 trades in earlier packets.

## Limits

- Native-SOL quote only. The token-quote path of `trade_v3`
  (`validate_buyback_fee_recipient_account`, which reads the ATA owner) and
  `multi_hop_curve_swap` are not run.
- In the `default-pubkey` row, the v2 handlers derive the WSOL ATA of the
  default key, whose bump is not forced to 255. Compare that row only between
  the two images, not with the other rows.
- One loader (upgradeable). Synthetic state.

## Reproduce

```
python3 producer.py --root <repo> --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}' --out .
python3 verify.py --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}'
```

The producer output is byte-identical across runs. verify.py first checks both
image sha256 values against `runtime/report.json.gz`. It then replays all 60
cases × 2 images (120 receipts) and compares each receipt byte for byte. Last,
it recomputes the summary, including `cu_by_slot`, which the table above is
read from. It exits 0 on success and 1 on any difference.

Files: `producer.py`, `verify.py`, `runtime/plan.json.gz`,
`runtime/receipts-upgradeable.jsonl.gz` and `runtime/report.json.gz`
(summary, `cu_by_slot`, per-case rows with lamport deltas and TradeEvents).
