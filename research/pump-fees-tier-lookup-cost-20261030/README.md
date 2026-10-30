# Pump Fees: compute-unit cost of the fee-tier lookup in `get_fees` / `get_fees_with_quote_mint`

## Question

`get_fees` and `get_fees_with_quote_mint` decode the FeeConfig and pick a fee
tier by market cap. What do they cost in compute units (CU), and how does the
cost change with the number of stored tiers and with the tier that gets
selected? Does the rebuilt image cost exactly the same as the deployed one at
every point?

Earlier packets and the repository harnesses check what these queries
**return**: tier boundaries, quote routing, layout sizes (#1907, and
`scripts/validate_fee_selection.py` / `scripts/validate_quote_fees.py`). None of them measures how the cost
grows with the tier lists. That matters because pump and pump_amm call these
queries by CPI on every trade. This packet sweeps the list lengths and the
selected index, then fits a cost model to the measured CU.

## Cases

There are 57 cases and 714 query transactions. Each one runs on both images:
the deployed original and the rebuilt candidate. A case writes one synthetic
FeeConfig at the pump `fee_config` PDA and then sends read-only queries to it.

- N = number of normal tiers and M = number of stable tiers.
- Tier i of a ladder has threshold `100 + 100·i` and fees `(base+i, i, 1)`, so
  every tier returns a distinct value.
- The account is 4097 bytes unless stated otherwise.
- The payer is a fixed seed (227). The clock is fixed.

| family | cases | what varies |
|---|---|---|
| `n-*` normal scan | 18 | N = 1..50 on the WSOL route; N = 1/10/50 on the quote-default-key and legacy `get_fees` routes. Every selectable k is queried with cap = threshold of tier k, plus cap 0 (below tier 0) and cap = u128 max. |
| `s-*` stable scan | 10 | M = 1..50 on the USDC route; M = 1/10/50 on legacy `get_fees` with `is_new_quote_mint` = 1. |
| `w-*` worst case | 5 | N = M = 50 (the most a 4097-byte FeeConfig holds), every scanning route, k = 0/25/49, below and top. |
| `x-*` cross | 9 | Length of the list that is **not** searched (M = 0..50 for normal queries, N = 1..50 for stable queries). |
| `f-*` flat | 4 | Routes that never scan a list (`is_pump_pool` = false, exotic quotes MINT77/USDT, exotic fees zero), at 1+1 and 50+50 tiers. |
| `a-*` allocation | 7 | Account length 2512, 2513, 4072, 4073, 4097, 8192, 10240, with N = M = 10 in all of them. |
| `z-*` layout | 2 | First threshold 0, and all ten thresholds equal. |
| `e-*` empty | 2 | Searched list empty. This is the known panic path from #1907. |

## Results

### Original vs rebuild

- **52 of 57 cases match** on every behavior field (error, Anchor error,
  return data, full log list, FeeConfig sha256) and on CU.
- **5 steps in 5 cases differ.** All five are the index-out-of-bounds panic on
  an empty tier list. In each one the panic location string differs and the
  rebuild uses 16 more CU:

| case | route | why the list is empty | CU original | CU rebuild | log line original | log line rebuild |
|---|---|---|---|---|---|---|
| `e-empty-normal` | WSOL | N = 0 | 4558 | 4574 | `panicked at pump-fees-math/src/lib.rs:49:23` | `panicked at programs/pump-fees/pump-fees-math/src/lib.rs:49:23` |
| `e-empty-stable` | USDC | M = 0 | 4609 | 4625 | same | same |
| `a-alloc-2512` | USDC | legacy layout, stable list not decoded | 4997 | 5013 | same | same |
| `a-alloc-2513` | USDC | legacy layout | 4997 | 5013 | same | same |
| `a-alloc-4072` | USDC | legacy layout | 4997 | 5013 | same | same |

- **Where it comes from.** The panic is `tiers[0]` on an empty slice in
  `select_fee_tier` (`programs/pump-fees/pump-fees-math/src/lib.rs`; original
  SBF range `0xab158..0xab2d0` per `recovered/fee_selection.rs`).
- The rebuild's panic path string is 19 bytes longer (`programs/pump-fees/`
  prefix). This is the same build-path root as the panic difference reported
  in #1907.
- This packet does not show whether the +16 CU comes from the longer string
  or from something else in the panic path. It only shows that the two always
  appear together here: 5 of 5 panics, and 0 of 709 non-panic steps.
- **Every non-panic step (709 of 714) has identical CU on both images.**

### Cost model (measured, both images)

For every successful scan on a 4097-byte FeeConfig, the measured CU fits:

    CU = A(route) + 50·(N + M) + 14·d

Here d is the number of tiers the reverse scan steps past before it matches
(d = len − 1 − k). B = 50 and C = 14 come from the scan families alone. The
residuals are then taken over every 4097-byte point, including the cross and
worst-case families that were not used to fit.

| route | instruction / argument | points | A | B (per stored tier) | C (per tier scanned past) | max abs residual |
|---|---|---|---|---|---|---|
| `legacy-opt0-normal` | `get_fees`, `is_new_quote_mint` = 0 | 64 | 3200 | 50 | 14 | normal-scan 0, worst-case 0 |
| `legacy-opt1-stable` | `get_fees`, `is_new_quote_mint` = 1 | 64 | 3201 | 50 | 14 | stable-scan 0, worst-case 0 |
| `quote-usdc-stable` | `get_fees_with_quote_mint`, quote USDC | 154 | 3337 | 50 | 14 | allocation 0, cross 0, stable-scan 0, worst-case 0 |
| `quote-wsol-normal` | `get_fees_with_quote_mint`, quote WSOL | 266 | 3286 | 50 | 14 | allocation 0, cross 42, layout 0, normal-scan 0, worst-case 0 |
| `quote-zero-normal` | `get_fees_with_quote_mint`, quote default key | 64 | 3261 | 50 | 14 | normal-scan 0, worst-case 0 |

The only off-model points (612 points in total) are both steps of
`x-normal10-stable0`. With the **other** list empty (M = 0), the query costs
42 CU less than the model predicts (3870 vs 3912, and 3744 vs 3786). Going
from M = 0 to M = 1 costs 92 CU. Each further tier costs 50.

What the model means, as measured:

- **Every stored tier costs 50 CU, in both lists, whichever list is
  searched.** Decoding the FeeConfig (`src/types.rs:168-170` →
  `read_full`) materializes both vectors.
  - The flat routes never scan, but they still pay it. `f-flat-routes-1-1`
    costs 3289 and `f-flat-routes-50-50` costs 8189 (`is_pump_pool` = false,
    WSOL), which is +4900 for 98 more tiers.
- **The scan runs from the top.** Selecting the highest tier is cheapest, and
  each lower tier adds 14 CU. This matches the reverse iterator in
  `select_fee_tier`.
  - Cap below tier 0's threshold returns early, 20 CU under the top hit
    (3366 vs 3386 at N = 1).
  - Cap = u128 max costs 3 CU more than an exact top-threshold hit (3389 vs
    3386).
- **When tier 0's threshold is 0, the early return can never fire.** In
  `z-first-threshold-zero-10`, cap 0 selects tier 0 only after scanning past
  all 9 higher tiers (3962 CU, the deepest point).
  - With all ten thresholds equal (`z-equal-thresholds-10`), cap 500 returns
    the **last** entry (1009, 9, 1) at depth 0 (3836 CU).
- **Worst case:** 9023 CU. That is `get_fees_with_quote_mint` with quote
  USDC, N = M = 50, and the selected stable tier is tier 0.

| case | N | M | CU k=N-1 (orig / rebuild) | CU k=0 (orig / rebuild) | cap below tier 0 | cap u128 max |
|---|---|---|---|---|---|---|
| `n-wsol-normal-1` | 1 | 1 | 3386 / 3386 | 3386 / 3386 | 3366 | 3389 |
| `n-wsol-normal-2` | 2 | 1 | 3436 / 3436 | 3450 / 3450 | 3416 | 3439 |
| `n-wsol-normal-3` | 3 | 1 | 3486 / 3486 | 3514 / 3514 | 3466 | 3489 |
| `n-wsol-normal-5` | 5 | 1 | 3586 / 3586 | 3642 / 3642 | 3566 | 3589 |
| `n-wsol-normal-8` | 8 | 1 | 3736 / 3736 | 3834 / 3834 | 3716 | 3739 |
| `n-wsol-normal-10` | 10 | 1 | 3836 / 3836 | 3962 / 3962 | 3816 | 3839 |
| `n-wsol-normal-16` | 16 | 1 | 4136 / 4136 | 4346 / 4346 | 4116 | 4139 |
| `n-wsol-normal-25` | 25 | 1 | 4586 / 4586 | 4922 / 4922 | 4566 | 4589 |
| `n-wsol-normal-32` | 32 | 1 | 4936 / 4936 | 5370 / 5370 | 4916 | 4939 |
| `n-wsol-normal-40` | 40 | 1 | 5336 / 5336 | 5882 / 5882 | 5316 | 5339 |
| `n-wsol-normal-49` | 49 | 1 | 5786 / 5786 | 6458 / 6458 | 5766 | 5789 |
| `n-wsol-normal-50` | 50 | 1 | 5836 / 5836 | 6522 / 6522 | 5816 | 5839 |
| `n-quote-zero-normal-1` | 1 | 1 | 3361 / 3361 | 3361 / 3361 | 3341 | 3364 |
| `n-quote-zero-normal-10` | 10 | 1 | 3811 / 3811 | 3937 / 3937 | 3791 | 3814 |
| `n-quote-zero-normal-50` | 50 | 1 | 5811 / 5811 | 6497 / 6497 | 5791 | 5814 |
| `n-legacy-opt0-normal-1` | 1 | 1 | 3300 / 3300 | 3300 / 3300 | 3280 | 3303 |
| `n-legacy-opt0-normal-10` | 10 | 1 | 3750 / 3750 | 3876 / 3876 | 3730 | 3753 |
| `n-legacy-opt0-normal-50` | 50 | 1 | 5750 / 5750 | 6436 / 6436 | 5730 | 5753 |
| `s-quote-usdc-stable-1` | 1 | 1 | 3437 / 3437 | 3437 / 3437 | 3417 | 3440 |
| `s-quote-usdc-stable-2` | 1 | 2 | 3487 / 3487 | 3501 / 3501 | 3467 | 3490 |
| `s-quote-usdc-stable-5` | 1 | 5 | 3637 / 3637 | 3693 / 3693 | 3617 | 3640 |
| `s-quote-usdc-stable-10` | 1 | 10 | 3887 / 3887 | 4013 / 4013 | 3867 | 3890 |
| `s-quote-usdc-stable-25` | 1 | 25 | 4637 / 4637 | 4973 / 4973 | 4617 | 4640 |
| `s-quote-usdc-stable-49` | 1 | 49 | 5837 / 5837 | 6509 / 6509 | 5817 | 5840 |
| `s-quote-usdc-stable-50` | 1 | 50 | 5887 / 5887 | 6573 / 6573 | 5867 | 5890 |
| `s-legacy-opt1-stable-1` | 1 | 1 | 3301 / 3301 | 3301 / 3301 | 3281 | 3304 |
| `s-legacy-opt1-stable-10` | 1 | 10 | 3751 / 3751 | 3877 / 3877 | 3731 | 3754 |
| `s-legacy-opt1-stable-50` | 1 | 50 | 5751 / 5751 | 6437 / 6437 | 5731 | 5754 |
| `w-full-quote-wsol-normal` | 50 | 50 | 8286 / 8286 | 8972 / 8972 | 8266 | 8289 |
| `w-full-quote-zero-normal` | 50 | 50 | 8261 / 8261 | 8947 / 8947 | 8241 | 8264 |
| `w-full-legacy-opt0-normal` | 50 | 50 | 8200 / 8200 | 8886 / 8886 | 8180 | 8203 |
| `w-full-quote-usdc-stable` | 50 | 50 | 8337 / 8337 | 9023 / 9023 | 8317 | 8340 |
| `w-full-legacy-opt1-stable` | 50 | 50 | 8201 / 8201 | 8887 / 8887 | 8181 | 8204 |

All CU per k are in `runtime/report.json.gz` (`cases[].cu_original` /
`cu_candidate`). Every intermediate k is on the model line.

### Account length (N = M = 10, same serialized tiers)

The layout is chosen by the data length (`src/types.rs:168-170`). Below 4073
bytes (`buf.len() < 4065` after the discriminator), only the normal list is
decoded. From 4073 to 4096 bytes, the stable list is decoded too. From 4097
bytes, the exotic fees are decoded as well.

| allocation | WSOL cap 100 (k=0) | WSOL cap 1000 (k=9) | USDC cap 1000 (k=9) | match |
|---|---|---|---|---|
| 2512 | ok 3808 | ok 3682 | panic 4997 / 5013 | USDC step no |
| 2513 | ok 3808 | ok 3682 | panic 4997 / 5013 | USDC step no |
| 4072 | ok 3808 | ok 3682 | panic 4997 / 5013 | USDC step no |
| 4073 | ok 4382 | ok 4256 | ok (2009,9,1) 4307 | yes |
| 4097 | ok 4412 | ok 4286 | ok (2009,9,1) 4337 | yes |
| 8192 | ok 4412 | ok 4286 | ok (2009,9,1) 4337 | yes |
| 10240 | ok 4412 | ok 4286 | ok (2009,9,1) 4337 | yes |

- On the legacy layout the stored stable bytes are ignored. A USDC query then
  panics on the empty list, and a normal query costs 604 CU less than at 4097.
- The stable-without-exotic layout (4073) costs 30 CU less than the full
  layout.
- Trailing bytes beyond the serialized data cost nothing (8192 and 10240 are
  the same as 4097).
- The 2512/4072/4073 return-value behavior was already reported in #1907.
  Here it is re-measured with CU.

### Cross and flat routes

| case | step | outcome | CU orig | CU rebuild |
|---|---|---|---|---|
| `x-normal10-stable0` | WSOL k=0 / k=9 | ok | 3870 / 3744 | 3870 / 3744 |
| `x-normal10-stable1` | WSOL k=0 / k=9 | ok | 3962 / 3836 | 3962 / 3836 |
| `x-normal10-stable10` | WSOL k=0 / k=9 | ok | 4412 / 4286 | 4412 / 4286 |
| `x-normal10-stable25` | WSOL k=0 / k=9 | ok | 5162 / 5036 | 5162 / 5036 |
| `x-normal10-stable50` | WSOL k=0 / k=9 | ok | 6412 / 6286 | 6412 / 6286 |
| `x-stable10-normal1` | USDC k=0 / k=9 | ok | 4013 / 3887 | 4013 / 3887 |
| `x-stable10-normal10` | USDC k=0 / k=9 | ok | 4463 / 4337 | 4463 / 4337 |
| `x-stable10-normal25` | USDC k=0 / k=9 | ok | 5213 / 5087 | 5213 / 5087 |
| `x-stable10-normal50` | USDC k=0 / k=9 | ok | 6463 / 6337 | 6463 / 6337 |
| `f-flat-routes-1-1` | pool=0 WSOL / `get_fees` pool=0 / MINT77 / USDT | (11,22,33) ×2, (44,55,66) ×2 | 3289 / 3258 / 3401 / 3401 | same |
| `f-flat-routes-50-50` | same four | same values | 8189 / 8158 / 8301 / 8301 | same |
| `f-flat-routes-exotic-zero-1-1` | MINT77 / USDT | (11,22,33) flat fallback | 3404 / 3404 | same |
| `f-flat-routes-exotic-zero-50-50` | MINT77 / USDT | (11,22,33) flat fallback | 8304 / 8304 | same |

## Reproduce

```
python3 producer.py --root <repo> --images '{"original": "<deployed.so>", "candidate": "<candidate.so>"}' --out <packet dir>
python3 verify.py --images '{"original": "<deployed.so>", "candidate": "<candidate.so>"}'
```

- `--images` also accepts a path to a file that holds that JSON object.
- `producer.py` checks the discriminators against
  `evidence/upstream/pump_fees.json` under `--root`.
- `verify.py` needs only the packet and the two images. It:
  1. checks both image sha256 values against the report;
  2. checks that the stored case list equals `producer.cases()`;
  3. replays every step on both images and compares it field by field with
     the receipts;
  4. rebuilds both runtime files and compares them byte for byte.
- It exits 0 on success and 1 on any difference.
- Two negative checks were run, and each exited 1: swapping the two images,
  and adding 1 to a single stored compute-unit value.

Images:

- **original:** `evidence/original/pump_fees/deployed.so`, sha256
  `4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e`.
- **candidate:** the rebuild, sha256
  `7a14f41440c60ac6e95053e9fdc712376a1eac3447ec2de6fa29b1b6ec654900`.
  - Built with `scripts/build_partial_candidate.py`, platform-tools v1.44 /
    cargo-build-sbf 2.1.21.
  - Source tree `7eb3b25ef7ee45dcba86f2af79344297e98a091d`, repo commit
    `aba9e07e8872a53ebfdeffc7cc5bfa20714fc053`.

Runtime: solders 0.27.1 LiteSVM, default compute budget. Two producer runs
gave byte-identical `runtime/` files.

## Limits

- The FeeConfig state is synthetic, written with `set_account`. Thresholds
  are sorted, as the setters require. Unsorted lists are covered by the
  return-value tests elsewhere.
- CU is measured for top-level calls. A CPI from pump or pump_amm adds that
  caller's own invoke overhead on top of these numbers. That overhead is not
  measured here.
- The model is an exact fit to the measured points. It is not derived from
  the bytecode. Points outside the measured ranges (N, M > 50 need an account
  above 4097 bytes) are not claimed.
