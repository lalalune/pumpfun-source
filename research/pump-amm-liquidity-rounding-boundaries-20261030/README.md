# pump_amm single-hop deposit / withdraw: ratio, rounding and error-path boundaries

## Question

The `amm-multi-hop-*` packets only touch `deposit` / `withdraw` as setup steps
inside multi-hop chains. This packet measures the two liquidity handlers on their
own: the ceil (deposit) and floor (withdraw) LP-ratio rounding, the slippage limits
at exactly the limit and one unit past it, accrued fees left out of the quote
reserve, the boosted-pool `virtual_quote_reserves` rescale (floor on deposit, ceil
on withdraw), the `disable_flags` bits, the seed-lock check, and every checked-math
error site the handlers can reach. Each case runs on the original image and on the
rebuild. For each case the packet records the error, the compute units, the full log
and the post-state of the pool, the LP mint and all five token accounts.

Images:

| role | sha256 | provenance |
|---|---|---|
| original | `6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7` | `evidence/original/pump_amm/deployed.so` |
| candidate | `384737bdc6c54cca4330fd5ce15f8c556a40a78afa6a93a69fe47d2b18527ab5` | `scripts/build_partial_candidate.py`, platform-tools v1.44 / cargo-build-sbf 2.1.21, source tree `755200a0d9fffe6f82a43fb65cc452d164f6e90b` (repo commit `1e04f5b34aa33c53f2b20b4200ba4ba266b4203e`) |

## Setup

- No captured fixtures and no RPC. `producer.py` builds every account itself: a 949-byte
  GlobalConfig (only `disable_flags` varies), a 300-byte Pool at its canonical
  `["pool", index, creator, base_mint, quote_mint]` PDA, classic SPL base/quote mints
  (decimals 6 / 9), a Token-2022 LP mint whose authority is the pool, and 165-byte token
  accounts. Keys are fixed byte patterns. The user keypair comes from a fixed seed.
- Each case runs in a fresh `LiteSVM` (solders 0.27.1) with its built-in SPL Token and
  Token-2022 programs and the clock fixed at unix time 1234567890.
- Defaults: pool base reserve B = 10^12, quote vault Q = 10^11, `pool.lp_supply` S =
  10^10, LP mint supply = S, user LP = S/2, `virtual_quote_reserves` V = 0, no accrued
  fees. Every case changes only the parameters listed in its receipt (`params`).
- Compared per case: error, post-state (pool and LP-mint bytes, five token balances),
  full log list, and compute units.

## Result

| measure | value |
|---|---|
| cases | 57 (30 deposit, 27 withdraw) |
| same error + same post-state | **57 / 57** |
| identical log list | 34 / 57 |
| identical log list after rewriting `thrown in programs/pump-amm/src/` -> `thrown in src/` and dropping the `consumed N of 200000` lines | **57 / 57** |
| identical compute units | 34 / 57 |
| CU delta (candidate - original) histogram | 0: 34, **-18: 13, -122: 10** |
| original with the 18-byte path prefix removed (in-memory control) vs rebuild: same CU and full logs | **57 / 57** |

Every success path (29 cases) and every token-program failure (5 cases: SPL
errors 1 and 14) uses the same CU on both images. All 23 log/CU mismatches are
AnchorError paths in pump_amm. On those paths the error number and the error line
are the same on both images. Only the file prefix and the CU differ.

### Mismatch 1: source-path prefix in the AnchorError log (-18 CU on 13 + 10 cases)

The original logs `AnchorError thrown in programs/pump-amm/src/...`, the rebuild logs
`AnchorError thrown in src/...`. The line numbers are the same. The missing prefix
`programs/pump-amm/` is 18 bytes long, which equals the -18 CU delta: the log
syscall charges per byte for a message this long. In `runtime/report.json.gz`
(`image_compare`), the original image contains `programs/pump-amm/src/` 33 times and
the rebuild 0 times. The rebuild's `.rodata` is 25,123 bytes against the original's
25,715 (-592). The source of the prefix difference is the build layout:
`programs/pump-amm/Cargo.toml` declares its own `[workspace]`, so `file!()` is
relative to the crate directory when `build_partial_candidate.py` builds it. The
original's paths are relative to a directory that contains `programs/`.

### Mismatch 2: a further -104 CU in 10 cases at 9 error sites (total -122)

| case | error | site (original line) | CU original | CU rebuild | delta |
|---|---|---|---|---|---|
| dep-truncation-base | 6024 Truncation | deposit.rs:77 | 13972 | 13850 | -122 |
| dep-truncation-quote | 6024 Truncation | deposit.rs:91 | 14278 | 14156 | -122 |
| dep-lp-supply-overflow | 6023 Overflow | deposit.rs:143 | 35483 | 35361 | -122 |
| dep-boost-negative-total | 6023 Overflow | deposit.rs:152 | 35589 | 35467 | -122 |
| dep-boost-i128-large | 6023 Overflow | deposit.rs:154 | 36245 | 36123 | -122 |
| wd-supply-0 | 6025 DivisionByZero | curve/constant_product.rs:112 | 13742 | 13620 | -122 |
| wd-truncation-base | 6024 Truncation | withdraw.rs:84 | 13963 | 13841 | -122 |
| wd-boost-negative-total | 6023 Overflow | withdraw.rs:160 | 35790 | 35668 | -122 |
| wd-boost-negative-total-large | 6023 Overflow | withdraw.rs:160 | 27300 | 27178 | -122 |
| wd-boost-change-truncation | 6024 Truncation | withdraw.rs:166 | 37170 | 37048 | -122 |

The 13 cases (10 distinct sites) that differ by exactly -18:

| case | error | site | CU original | CU rebuild |
|---|---|---|---|---|
| dep-disabled-flag2, dep-flags-255 | 6018 DisabledDeposit | deposit.rs:56 | 13653 | 13635 |
| dep-base-limit-minus-1 | 6004 ExceededSlippage | deposit.rs:79 | 15176 | 15158 |
| dep-quote-limit-minus-1 | 6004 ExceededSlippage | deposit.rs:100 | 15596 | 15578 |
| dep-fees-sum-overflow | 6023 Overflow | state/pool.rs:408 | 13572 | 13554 |
| dep-fees-exceed-vault | 6023 Overflow | state/pool.rs:417 | 13574 | 13556 |
| dep-supply-0 | 6025 DivisionByZero | curve/fees.rs:21 | 13675 | 13657 |
| wd-disabled-flag4, wd-flags-255 | 6019 DisabledWithdraw | withdraw.rs:57 | 13658 | 13640 |
| wd-seed-lock-mint-gt-pool | 6067 SeedLockViolation | withdraw.rs:62 | 15257 | 15239 |
| wd-base-limit-plus-1 | 6004 ExceededSlippage | withdraw.rs:86 | 15163 | 15145 |
| wd-quote-limit-plus-1 | 6004 ExceededSlippage | withdraw.rs:107 | 15579 | 15561 |
| wd-fees-exceed-vault | 6023 Overflow | state/pool.rs:417 | 13583 | 13565 |

All 9 -122 sites are `map_err(|_| error!(..))` / `ok_or_else(|| error!(..))` errors
built inside the `deposit` / `withdraw` handler bodies, plus `liquidity_floor_ratio`
(constant_product.rs:112), which only `withdraw` calls. The `require!` /
`require_gte!` sites in the same handlers show only -18, and so do the Pool helpers
(pool.rs:408/417) and `ceil_div` (fees.rs:21).

### Control: the original with the path prefix removed accounts for the full delta

`image_compare` shows `.text` with the same length in both images (1,162,040 bytes,
145,255 8-byte slots), but 73,880 slots differ. To test whether the residual is code
or data, `producer.py` builds a control image in memory from the original, with
nothing written to disk. In it, every `lddw` that loads a
`programs/pump-amm/src/*.rs` string is moved 18 bytes later, past the prefix, and
the matching length immediate is lowered by 18. This patches 245 sites, and the
control's sha256 is `f470afd6...1e24`. The control's file names then read `src/...`
exactly as the rebuild's. Nothing else changes. Results from
`stripped_original_control` in the report:

| control vs rebuild | value |
|---|---|
| same error + post-state | 57 / 57 |
| identical full log list (including the CU lines) | **57 / 57** |
| identical CU | **57 / 57** |
| original CU - control CU | 0: 34, 18: 13, **122: 10** |

So the whole -18 / -122 difference is the 18-byte-longer file string in the
original. In the 10 closure-error cases, that string costs 104 CU of per-byte
work before the log call, about 5.8 CU per byte. The -18 sites do not do this work.
No CU or log difference is left that would point at handler code in these paths.
Making the rebuild's log and CU byte-equal on these paths takes no code change, only
a build with the original workspace layout, for example a build from a workspace
root above `programs/`.

### Rounding and boundary behavior (identical on both images)

The values are from `observed` in the report: token movement into the pool, the
user's LP change, `pool.lp_supply` after the instruction and `virtual_quote_reserves`
after.

| case | inputs (non-default) | base to pool | quote to pool | LP to user | lp_supply after | V after |
|---|---|---|---|---|---|---|
| dep-amount-1-ceil | amount 1 | 100 | 10 | 1 | 10000000001 | 0 |
| dep-amount-1-ceil-up | B 10^12+1, Q 10^11+1, amount 1 | 101 | 11 | 1 | 10000000001 | 0 |
| dep-small-pool-ceil | B 3, Q 7, S 2, amount 1 | 2 | 4 | 1 | 3 | 0 |
| dep-amount-0 | amount 0 | 0 | 0 | 0 | 10000000000 | 0 |
| dep-base-limit-exact | B 10, Q 10, S 3, amount 3, base_limit 10 | 10 | 10 | 3 | 6 | 0 |
| dep-quote-limit-exact | B 10, Q 10, S 3, amount 1, quote_limit 4 | 4 | 4 | 1 | 4 | 0 |
| dep-fees-excluded | pf = cf = 10^10, V -2*10^10, amount 10^6 | 100000000 | 8000000 | 1000000 | 10001000000 | -20000000000 |
| dep-fees-eq-vault | pf+cf = Q, amount 10^6 | 100000000 | 0 | 1000000 | 10001000000 | -100000000000 |
| dep-boost-floor | V 1000007, amount 3 | 300 | 30 | 3 | 10000000003 | 1000007 |
| dep-boost-with-fees | V 5*10^9, pf = cf = 10^9, amount 10^6 | 100000000 | 9800000 | 1000000 | 10001000000 | 5000700000 |
| wd-amount-1 | amount 1 | -100 | -10 | -1 | 9999999999 | 0 |
| wd-floor-down | B 10^12-1, Q 10^11-1, amount 1 | -99 | -9 | -1 | 9999999999 | 0 |
| wd-small-pool-floor | B 3, Q 7, S 2, amount 1 | -1 | -3 | -1 | 1 | 0 |
| wd-all-supply | amount = S | -1000000000000 | -100000000000 | -10000000000 | 0 | 0 |
| wd-pool-gt-mint | LP mint supply S-1 | -100000000 | -10000000 | -1000000 | 9999000000 | 0 |
| wd-boost-ceil | V 1000007, amount 3 | -300 | -30 | -3 | 9999999997 | 1000006 |
| wd-boost-ceil-one | V 9, amount 1 | -100 | -10 | -1 | 9999999999 | 8 |
| wd-boost-with-fees | V 5*10^9, pf = cf = 10^9, amount 10^6 | -100000000 | -9800000 | -1000000 | 9999000000 | 4999300000 |

Notes, all measured:
- Deposit rounds both legs up, and withdraw rounds both legs down. With B = 3,
  Q = 7, S = 2, one LP unit costs 2 / 4 and redeems 1 / 3.
- The quote reserve used for the ratio is `vault - protocol_fees - creator_fees`.
  When the accrued fees equal the vault (`dep-fees-eq-vault`), the deposit succeeds
  with 0 quote in. One unit above that, the deposit fails with 6023 at pool.rs:417.
- The `virtual_quote_reserves` rescale uses `V + protocol_fees + creator_fees`. On
  deposit it rounds down: V = 9 with 1 LP unit out of 10^10 leaves V at 9. On
  withdraw it rounds up: the same input moves V from 9 to 8. A negative
  `V + fees` fails with 6023 on both handlers (deposit.rs:152 / withdraw.rs:160)
  after the token CPIs have run (35,589 / 35,790 CU on the original).
- `disable_flags` bit 2 blocks only deposit (6018) and bit 4 only withdraw (6019).
  The other handler is unaffected (`dep-flag4-only`, `wd-flag2-only`).
- Withdraw requires `pool.lp_supply >= lp_mint.supply` (6067 when the mint is one
  above). A pool supply above the mint supply passes (`wd-pool-gt-mint`).
- `dep-lp-mint-to-overflow` fails inside the Token-2022 `mint_to` (SPL error 14)
  before pump_amm's own `lp_supply` add. The CU is identical on both images (34,026).

## Files

- `producer.py` builds the accounts, runs the 57 cases on both images and writes
  `runtime/receipts.jsonl.gz` (one receipt per case with full logs and post-state)
  and `runtime/report.json.gz` (summary, per-case table, image sha256s, ELF section
  comparison, prefix-stripped control). Each receipt also carries the control's CU
  and whether its error, state and logs equal the rebuild's.
- `verify.py` checks the image sha256s against the report, re-runs every case through
  `producer.produce` and requires byte-identical receipts and the same ELF comparison.

## Reproduce

```
python3 producer.py --root <repo> --images '{"original": "<repo>/evidence/original/pump_amm/deployed.so", "candidate": "<candidate.so>"}' --out <packet>
python3 verify.py --images '{"original": "<repo>/evidence/original/pump_amm/deployed.so", "candidate": "<candidate.so>"}'
```

Two producer runs gave byte-identical `runtime/` files. `--root` is accepted for the
common packet interface. The cases use no repository file besides the two images.
