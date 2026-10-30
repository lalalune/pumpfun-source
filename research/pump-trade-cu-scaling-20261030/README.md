# Pump Main: trade compute-unit scaling, original vs rebuild (2026-10-30)

## Question

Earlier Pump Main packets measured trade *boundaries*: one amount per rule,
and whether each case passes or fails. This packet asks something different.
When one operand of a trade is swept over orders of magnitude, does the
rebuild's compute-unit (CU) cost follow the original's? And which code branch
carries the small CU differences that remain on successful v2 trades?

The operands swept are:

- the token amount (10^0 .. 10^14);
- the lamport input of `buy_exact_sol_in` (10^3 .. 10^11);
- the curve reserve magnitude (`virtual_token_reserves` 10^10 .. 10^18, where
  the `amount * virtual_quote_reserves` product leaves u64);
- the protocol and creator fee basis points;
- whether the creator vault is already rent-exempt.

Handlers measured: legacy `buy`, `sell`, `buy_exact_sol_in`, and native-SOL
`buy_v2`, `sell_v2`.

## Images

| | sha256 | bytes |
|---|---|---:|
| original `evidence/original/pump/deployed.so` | `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d` | 10,485,715 |
| rebuild `<candidate.so>` | `ae713165a56752f7e1c6153137842e2b145885180b5c71e21a342afed45bd44b` | 1,934,928 |

The rebuild was built by `scripts/build_partial_candidate.py` (platform-tools
v1.44 / cargo-build-sbf 2.1.21) from source tree
`9e5d2900ed30981d5766fb101ef120ee198161be` at repo commit
`7e26cbf36c5c0c824e3eb36417ce8a35866f530a`.

## Setup

- LiteSVM (solders 0.27.1). Pump runs under the upgradeable loader
  (program + programdata accounts, the mainnet layout). Under that loader the
  ELF size does not enter CPI cost.
- The pump_fees slot holds a 9-instruction SBPFv0 program that `producer.py`
  generates in memory (`fee_stub`). It returns the case's `fee_bps`
  (lp, protocol, creator) as the 24-byte `Fees` return value. Both images see
  the identical stub.
- All state is synthetic (IDL layouts). Keys come from fixed seeds, the clock
  is fixed, and every case runs in a fresh VM. The full initial account set of
  every case is in `runtime/plan.json.gz`.
- Default curve: `virtual_token_reserves` 1,073,000,000,000,000,
  `virtual_quote_reserves` 30,000,000,000. Global `buyback_basis_points` 5000.
  Default stub fees (0, 95, 30).

## Result

**60 cases. 0 behavior mismatches.** Error, return data, events, inner
instructions, account after-state and transaction bytes are equal on every
case. CU is equal on 46/60 cases. The other 14 are listed below; each one
differs only in its `consumed` log line, plus one AnchorError site line.

### 1. CU scales identically with operand magnitude

| series | cases | CU range, original | CU range, rebuild | orig - rebuild |
|---|---:|---|---|---|
| `amount/buy` (10^0..10^14 tokens) | 12 | 68,544 .. 70,781 | 68,544 .. 70,781 | 0 on all 12 |
| `amount/sell` (10^0..10^14 tokens) | 12 | 47,562 .. 52,558 | 47,562 .. 52,558 | 0 on all 12 |
| `amount/buy_exact_sol_in` (10^3..10^9 lamports, successes) | 4 | 71,743 .. 72,024 | 71,743 .. 72,024 | 0 on all 4 |
| `reserves/buy` (vtr 10^10..10^18) | 5 | 70,268 .. 70,794 | 70,268 .. 70,794 | 0 on all 5 |
| `reserves/sell` (vtr 10^10, 10^14, 10^18) | 3 | 52,132 .. 52,656 | 52,132 .. 52,656 | 0 on all 3 |
| `fee/buy` (6 fee triples) | 6 | 60,272 .. 70,701 | 60,272 .. 70,701 | 0 on all 6 |
| `amount/buy_v2` (10^0..10^14) | 4 | 93,227 .. 95,450 | 93,229 .. 95,452 | -2 on all 4 |
| `amount/sell_v2` (10^0..10^14) | 4 | 81,141 .. 84,341 | 81,141 .. 84,344 | 0 (10^0), -3 (others) |

Within each series the original and the rebuild move by exactly the same
amounts. The arithmetic itself, including the u128 path, has the same cost in
both images. The large steps come from transfer branches, which the
inner-instruction counts show:

- **legacy buy 10^6 -> 10^7 tokens: +2,000 CU** (68,546 -> 70,546). Inner
  instructions go 8 -> 9: the protocol fee becomes 3, so the buyback share
  (5000 bps) becomes nonzero and one more transfer runs.
- **legacy sell 10^4 -> 10^5 tokens: +4,643 CU** (47,562 -> 52,205). At
  amounts up to 10^4 the quote rounds to 0, the sell succeeds with zero
  lamports out and no fee transfers, and there are 3 inner instructions. At
  10^5 the quote is 2, the creator vault gets its rent top-up, and there are
  4 inner instructions.
- **fee/buy (0,0,0): 60,272 vs (0,95,30): 70,694**. With fees zero, no fee
  transfers run (5 inner instructions instead of 9).
- **reserves:** the CU change from vtr 10^14 to 10^16 is +254 (buy) on both
  images. That is the range where `amount * vqr` exceeds u64.

### 2. Where the remaining v2 CU differences are

| case | creator fee | creator vault before | CU original | CU rebuild | orig - rebuild |
|---|---:|---|---:|---:|---:|
| `v2fee/buy_v2/0-0-0` | 0 | absent | 86,768 | 86,767 | +1 |
| `v2fee/buy_v2/0-95-0` | 0 | absent | 90,754 | 90,753 | +1 |
| `v2fee/buy_v2/0-0-30` | 84 | absent (topped up) | 91,377 | 91,379 | -2 |
| `v2fee/buy_v2/0-0-30-vault-funded` | 84 | rent-exempt | 89,373 | 89,376 | -3 |
| `v2fee/sell_v2/0-0-0` | 0 | absent | 81,394 | 81,394 | 0 |
| `v2fee/sell_v2/0-95-0` | 0 | absent | 81,592 | 81,592 | 0 |
| `v2fee/sell_v2/0-0-30` | 84 | absent (topped up) | 84,143 | 84,146 | -3 |
| `v2fee/sell_v2/0-0-30-vault-funded` | 84 | rent-exempt | 82,139 | 82,143 | -4 |
| `v2fee/buy/0-0-30-vault-funded` (legacy control) | 84 | rent-exempt | 64,402 | 64,402 | 0 |

What the measurements show:

- **The difference follows the creator-fee branch (`if cf>0`)**, not the
  amount, the protocol fee or the buyback split. Turning only the creator fee
  on moves orig - rebuild by -3 (buy_v2: +1 -> -2; sell_v2: 0 -> -3).
- With the creator vault already rent-exempt, the rent top-up transfer is
  skipped (one fewer inner instruction). The branch then differs by -4
  (buy_v2: +1 -> -3; sell_v2: 0 -> -4).
- In the rebuild source this branch is `buy_v2.rs:507-509`, `buy_v2.rs:1001-1006`
  and `sell_v2.rs:391-395`. It calls `buy_v2::native_payments::ensure_rent_exempt(0, ..)`
  and then `pay_owned`.
- The legacy handlers use `legacy_buy::native_payments::ensure_rent_exempt` +
  `move_native` (`buy.rs:235`, `lib.rs:1040`). They show 0 difference with and
  without a funded vault.
- So the 3-4 CU sits in the v2 creator-payment helpers. **Which instructions
  inside them account for it was not measured**: LiteSVM gives no
  per-instruction trace here.
- buy_v2 also carries a separate +1 (original costs 1 CU more) that is present
  with all fees zero, so it lies outside the fee branches.
- These -2/-3 values on v2 successes match what earlier v2 packets reported.
  This packet attributes them to a branch.

### 3. Error path

| case | stop | CU original | CU rebuild | orig - rebuild | log line difference |
|---|---|---:|---:|---:|---|
| `amount/buy_exact_sol_in/1e11` | NotEnoughTokensToBuy (6021) | 42,767 | 42,649 | +118 | AnchorError site `programs/pump/src/buy.rs:151` vs `src/buy.rs:151` |

The site path is 14 bytes longer in the original (`programs/pump/`). The
+118 is the same single-`require!` gap that earlier Pump Main packets
reported on other handlers (for example create_v2 and migrate_v2). It is not
specific to scaling.

## Behaviors observed (equal on both images)

- A legacy sell of 1 .. 10^4 tokens on the default curve succeeds and
  transfers the tokens for a quote of 0 lamports (`minimum` = 0).
- The fee stub's protocol bps value is applied as returned. With bps
  2^31 - 1 a 27,960-lamport buy charges a protocol fee of 6,004,364,278.
  Real pump_fees does not return such values; this was already covered by the
  earlier post-fee packet.

## All cases

See `runtime/report.json.gz` (`loaders.upgradeable.cases`, and `series` for
the per-series ranges). Each case there has CU per image, error name, decoded
TradeEvent, curve after-state and lamport deltas.

## Reproduce

```
python3 producer.py --root <repo> --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}' --out <dir>
python3 verify.py --images '{"original": "<deployed.so>", "candidate": "<candidate.so>"}'
```

`producer.py` reads only `evidence/upstream/pump.json` from the repository,
to check instruction and account discriminators. Two runs give byte-identical
runtime files. `verify.py` uses only this folder and the two images. It checks
the image sha256 values, replays all 60 cases on both images, compares every
receipt byte for byte and recomputes the summary. It exits 0 on success.

## Overlap

- `pump-trade-post-fee-quote-boundaries-20261030`,
  `pump-buy-historical-curve-layouts-20261030` and
  `pump-sell-historical-curve-layouts-20261030` contain single-point trades on
  the same handlers. None of them sweeps one operand or splits the v2 CU
  difference by branch.
- `scripts/pump_buy_v2_differential.py` and `pump_sell_v2_differential.py`
  read the untracked `research/imported-lab` snapshot and report no CU-scaling
  series.
