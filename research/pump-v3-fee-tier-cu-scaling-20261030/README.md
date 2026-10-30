# Pump Main v3 trades: fee-tier and amount compute-unit scaling, original vs rebuild (2026-10-30)

## Question

`buy_v3`, `buy_exact_quote_in_v3` and `sell_v3` do not CPI pump_fees.
Instead they deserialize the pump_fees `FeeConfig` account themselves and
pick a market-cap fee tier with `calculate_fee_tier`
(`programs/pump/src/util/fee.rs:160-167`, a reverse scan:
`fee_tiers.iter().rev().find(|t| market_cap >= t.threshold)`). The CU cost of
that path therefore depends on account data that an admin controls (the tier
vector).

Earlier v3 packets (`pump-v3-trade-boundaries-20261030`,
`pump-v3-token-quote-boundaries-20261030`) checked which tier gets selected
on 2-tier configs. This packet measures **how the cost scales** on both
images. The sweeps are:

- the tier count n = 1..60 (60 fills the 2,512-byte minimum account);
- the selected tier position k among 60 tiers;
- the token amount and lamport input over orders of magnitude;
- the FeeConfig account length.

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

- LiteSVM (solders 0.27.1). Pump runs under the upgradeable loader. No
  pump_fees program is loaded: v3 reads FeeConfig as plain data.
- Native-SOL curve, synthetic IDL-layout state. Fixed keys and clock, one
  fresh VM per case. The full initial state is in `runtime/plan.json.gz`.
- Tier j charges protocol 50 + j bps and creator 20 bps. Thresholds are
  placed so that the market cap falls inside tier k, with a margin of at least
  mcap/(2k+1) on both sides. The TradeEvent fee confirms the selected tier: for
  example k = 0 -> 139,926 on a 27,985,075 quote (50 bps), and
  k = 59 -> 305,038 (109 bps).

## Result

**58 cases. 0 behavior mismatches.** Error, return data, events, inner
instructions, after-state and tx bytes are equal on every case. CU is equal
on 49/58 cases.

### 1. Tier cost model (equal on both images)

`report.loaders.upgradeable.tier_model` fits, per handler and image,

    CU = base + per_tier * (n - 1) + per_skipped_tier * (n - 1 - k)

| handler / image | base (n=1) | per_tier | per_skipped_tier | max abs residual (13 tier cases) |
|---|---:|---:|---:|---:|
| buy_v3 / original | 54,487 | 50 | 15 | 0 |
| buy_v3 / rebuild | 54,487 | 50 | 15 | 0 |
| sell_v3 / original | 51,875 | 50 | 15 | 0 |
| sell_v3 / rebuild | 51,875 | 50 | 15 | 0 |

The model reproduces every tier case exactly, on both images.

- With n tiers, every extra tier costs 50 CU, even when the selected tier is
  the last one (`tiers-last`: n = 1 -> 54,487, n = 60 -> 57,437 for buy_v3).
- With 60 tiers, every tier the reverse scan passes over before its match
  costs another 15 CU. So the *lowest* tier is the most expensive
  (`tiers-60/buy_v3`: k = 59 -> 57,437, k = 0 -> 58,322; spread 885 = 15 x 59).
  This matches the `rev().find` order at fee.rs:167.
- The 50-per-tier term is present whatever the scan length. That is
  consistent with a per-element decode of the tier vector, but this packet
  does not isolate it.
- The worst case measured (60 tiers, k = 0) is +3,835 CU over a single-tier
  config (58,322 vs 54,487).

### 2. Amount sweeps and FeeConfig length

| series | cases | CU original | CU rebuild | orig - rebuild |
|---|---:|---|---|---|
| `amount/buy_v3` (10^0..10^14 tokens) | 8 | 54,247 .. 54,575 | 54,247 .. 54,575 | 0 on all 8 |
| `amount/sell_v3` (10^0..10^14 tokens) | 8 | 51,523 .. 51,973 | 51,523 .. 51,973 | 0 on all 8 |
| `amount/buy_exact_quote_in_v3` (10^3..10^9 lamports) | 4 | 55,665 .. 55,946 | 55,666 .. 55,947 | -1 on all 4 |
| `length/buy_v3` (2,512 / 4,097 / 10,240 bytes) | 3 | 54,487 | 54,487 | 0 on all 3 |

- The account length beyond the parsed vectors does not change CU (0 spread).
- `buy_exact_quote_in_v3` costs the rebuild 1 CU more on every success,
  whatever the input magnitude. It is a constant offset, not scaling.
- The fee-branch split below shows the -1 does not depend on the fee
  branches either. It is -1 with protocol and creator fees on or off, while
  `buy_v3` is 0 on the same four tiers. So the offset is in the
  exact-quote-in path of trade_v3.rs, i.e. the code that derives the token
  amount from the quote budget, not in fee computation or payout. The exact
  instructions were not isolated.

| tier (protocol, creator bps) | buy_exact_quote_in_v3 CU orig / rebuild | diff | buy_v3 CU orig / rebuild | diff |
|---|---|---:|---|---:|
| (0, 0) | 55,577 / 55,578 | -1 | 54,385 / 54,385 | 0 |
| (95, 0) | 55,931 / 55,932 | -1 | 54,485 / 54,485 | 0 |
| (0, 30) | 55,834 / 55,835 | -1 | 54,387 / 54,387 | 0 |
| (95, 30) | 55,936 / 55,937 | -1 | 54,487 / 54,487 | 0 |
- sell_v3 of 1..10^4 tokens succeeds with a quote of 0 (both images).

### 3. Error path

| case | stop | CU original | CU rebuild | orig - rebuild | log line difference |
|---|---|---:|---:|---:|---|
| `amount/buy_exact_quote_in_v3/1e11` | NotEnoughTokensToBuy | 37,778 | 37,660 | +118 | AnchorError site `programs/pump/src/trade_v3.rs:506` vs `src/trade_v3.rs:506` |

## All cases

`runtime/report.json.gz` contains `loaders.upgradeable.cases` (CU per image,
TradeEvent, after-state, lamport deltas), `series` and `tier_model`.

## Reproduce

```
python3 producer.py --root <repo> --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}' --out <dir>
python3 verify.py --images '{"original": "<deployed.so>", "candidate": "<candidate.so>"}'
```

`producer.py` reads only `evidence/upstream/pump.json` from the repository,
to check discriminators. Two runs give byte-identical runtime files.
`verify.py` uses only this folder and the two images. It checks the image
sha256 values, replays all 58 cases on both images, compares every receipt
byte for byte, and recomputes the summary, including `tier_model`. It exits
0 on success.

## Overlap

- `pump-v3-trade-boundaries-20261030` covers tier *selection* boundaries
  (empty, below first, at first, at last) on 2-tier configs. This packet adds
  the cost model.
- `pump-fees-...` packets measure pump_fees' own `get_fees` cost, which is a
  different program and a different code path.
