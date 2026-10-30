# pump_amm `create_pool`: initial-liquidity `integer_sqrt`, minimum-liquidity boundary and pre-transfer checks

## Question

`create_pool` (`programs/pump-amm/src/instructions/create_pool.rs`) mints
`floor(sqrt(pool_base * pool_quote)) - 100` LP tokens to the creator
(`initial_liquidity`, l.330-340, `U128::integer_sqrt`; `checked_sub(100)`, l.290).
Before moving tokens it runs these checks: the mayhem and cashback gates
(l.171/177/183/189), the `disable_flags & 1` gate (l.193), zero amounts
(l.198/199), mint support (l.201/215) and `SameMint` (l.217). After the transfers
it runs the non-canonical creator-fee guard (l.279).
The existing create-pool packet (`amm-multi-hop-split-boost-tf-create-pool-chains-20261029`)
covers three inputs: 99/99, 100/100 and 10^12/10^12. This packet measures:

1. the square-root result and the compute cost across the whole u64 x u64 input range
   (decades 10^2..10^19, products up to (2^64-1)^2, non-square and asymmetric pairs);
2. the minimum-liquidity edge, using pairs whose product sits on either side of 100^2;
3. every pre-transfer error path in the handler, the order of those checks, and how the
   optional trailing arguments (`OptionBool`/`OptionU64`) are decoded.

All of this is compared between the original image and the rebuild.

## Images

| image | sha256 |
|---|---|
| original `evidence/original/pump_amm/deployed.so` | `6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7` |
| rebuild `<candidate.so>` (`scripts/build_partial_candidate.py`, platform-tools v1.44 / cargo-build-sbf 2.1.21, source tree `755200a0d9fffe6f82a43fb65cc452d164f6e90b`, repo commit `1e04f5b34aa33c53f2b20b4200ba4ba266b4203e`) | `384737bdc6c54cca4330fd5ce15f8c556a40a78afa6a93a69fe47d2b18527ab5` |

## Setup

Each case starts from a fresh LiteSVM (solders 0.27.1). The setup has:

- a synthetic 949-byte GlobalConfig. It uses `disable_flags`, `mayhem_mode_enabled`
  (offset 417) and `is_cashback_enabled` (offset 642) for the gates.
- plain 82-byte SPL Token base and quote mints, with decimals 6 and 9.
- user token accounts.
- LiteSVM's built-in SPL Token, Token-2022 and Associated Token programs.

The creator is a fixed-seed keypair, so every pool is **non-canonical**: the creator is
not the pump `pool_authority` PDA of the base mint. The pool, LP mint, user LP ATA and
both vault ATAs are created by the instruction itself. Pool index is 7.

For each case the producer records:

- the error and compute units;
- the full log list;
- the full Pool account bytes;
- LP mint supply, user LP, both vaults and both user balances;
- payer lamports.

An independent model (`math.isqrt(base*quote)`, `-100`) checks the minted amounts.

## Results (60 cases)

| measure | value |
|---|---|
| cases / successful creates | 60 / 39 |
| same error **and** same post-state (all accounts, Pool bytes, lamports) | **60 / 60** |
| model match (`lp_supply = isqrt(b*q)`, user LP `= lp_supply - 100`) on successes | 39 / 39 |
| logs identical (exact, and ignoring CU lines) | 42 / 60 |
| logs identical after normalizing `programs/pump-amm/src/` -> `src/` | 60 / 60 |
| CU equal | 42 / 60 |
| CU delta (rebuild - original) histogram | 0: 42, -18: 14, -122: 4 |
| control: original with the 18-byte path prefix stripped (245 `lddw` sites) - CU / logs / error+state equal to rebuild | 60 / 60, 60 / 60, 60 / 60 |

**Every successful path has the same CU in both images.** That covers 39 creates and
24 distinct CU values from 165,087 to 170,653.
The only CU or log differences are on the 18 AnchorError paths:

| cases | error (site in rebuild) | original CU | rebuild CU | delta |
|---|---|---|---|---|
| min-99-99 | TooLittlePoolTokenLiquidity 6003 (`create_pool.rs:290`) | 154,227 | 154,209 | -18 |
| min-99-101, min-1-9999, min-3-3333 | TooLittlePoolTokenLiquidity (`:290`) | 154,645 | 154,627 | -18 |
| min-1-1 | TooLittlePoolTokenLiquidity (`:290`) | 152,894 | 152,876 | -18 |
| err-disabled-flag1, err-disabled-and-base-0 | DisabledCreatePool 6017 (`:193`) | 134,098 | 134,080 | -18 |
| err-mayhem-disabled, err-mayhem-before-disabled | MayhemModeDisabled (`:171`) | 134,915 | 134,897 | -18 |
| err-mayhem-noncanonical | OnlyPumpPoolsMayhemMode (`:177`) | 134,933 | 134,915 | -18 |
| err-cashback-disabled | CashbackNotEnabled (`:183`) | 134,940 | 134,922 | -18 |
| err-cashback-noncanonical | OnlyPumpPoolsCashback (`:189`) | 134,933 | 134,915 | -18 |
| err-creator-fee-noncanonical | OnlyCanonicalPumpPoolsCanHaveCoinCreator (`:279`) | 154,258 | 154,240 | -18 |
| err-can-edit-noncanonical | OnlyCanonicalPumpPoolsCanHaveCoinCreator (`:279`) | 154,266 | 154,248 | -18 |
| err-base-0, err-both-0 | ZeroBaseAmount 6001 (`:198`, `require_gt!`, logs `Left: 0` / `Right: 0`) | 135,256 | 135,134 | -122 |
| err-quote-0 | ZeroQuoteAmount (`:199`, `require_gt!`) | 135,259 | 135,137 | -122 |
| err-same-mint | SameMint (`:217`, `require_keys_neq!`) | 102,894 | 102,772 | -122 |

**Cause.** The original logs `AnchorError thrown in programs/pump-amm/src/instructions/create_pool.rs:N`,
while the rebuild logs `... thrown in src/instructions/create_pool.rs:N`.
`programs/pump-amm/Cargo.toml` declares its own `[workspace]`, so `file!()` is
crate-relative in the `build_partial_candidate` rebuild. The prefix is 18 bytes.
The control image is the original with every reference to a
`programs/pump-amm/src/*.rs` string moved past the prefix and its length immediate
lowered by 18 (245 sites, nothing else changed). Its CU, logs, error and state equal the
rebuild's in all 60 cases. That includes the four −122 cases, which use the
value-comparing macros (`require_gt!`, `require_keys_neq!`). So the whole −18 and −122
comes from the longer file-name string in the original. No instruction or arithmetic in
`create_pool` differs in these runs.

### Behaviour pinned (identical in both images)

- **Square root.** In every success, `lp_supply = floor(sqrt(base*quote))` and the user
  LP is `lp_supply - 100`. That includes (2^64-1, 2^64-1) giving 18,446,744,073,709,551,615,
  (2^63, 2^63) giving 9,223,372,036,854,775,808, and (2^63, 2^63-1) giving
  9,223,372,036,854,775,807. The `Truncation` error at l.339 is never reached: the
  square root of a u64 x u64 product always fits in a u64. CU depends on the input
  (165,087 for 10^3/10^3 up to 170,653 for 2^63/2^63) and is identical between images.
- **Minimum liquidity.** The check is on the square root, not on the amounts. Products
  of at least 10,000 succeed: 100/100, 1/10,000, 3/3,334 (10,002), 100/101 and 1/10,200
  all give liquidity 100 and user LP 0. Products of 9,999 or less fail with 6003:
  99/101 (9,999), 1/9,999, 3/3,333, 99/99 and 1/1.
- **Check order.**
  - `disable_flags & 1` is checked before the zero amounts (flag 1 with base 0 gives
    DisabledCreatePool).
  - The mayhem gate is checked before the disable flag (mayhem + flag 1 + base 0 gives
    MayhemModeDisabled).
  - Zero base is checked before zero quote.
  - `disable_flags = 254` (bit 0 clear) creates normally.
  - These pre-transfer errors fire after Anchor has already run the `init` CPIs for the
    pool, LP mint and the three ATAs (about 134-135k CU), so the cost of a rejected create
    is paid anyway.
  - SameMint fires at 102,894 CU, because the shared vault ATA is created only once.
- **Non-canonical creator fee guard (l.279).** It runs after both token transfers.
  `creator_fee_bps = 1`, or `can_edit_creator_fee = true`, gives 6028
  OnlyCanonicalPumpPoolsCanHaveCoinCreator at 154,258 / 154,266 CU, and the whole
  transaction, including the transfers, is rolled back. `is_holder_reward = true` on a non-canonical pool succeeds with the same LP
  amounts in both images (source l.281 stores `canonical && holder`).
- **Optional trailing arguments.** Unless a case says otherwise, it sends the 59-byte form
  with no option bytes: index, the two amounts, `coin_creator` and `is_mayhem_mode`.
  The four `OptionBool`/`OptionU64` arguments then decode as false/0. With 1,000,000/1,000,000:
  - the 59-byte form costs 165,504 CU;
  - adding explicit `cashback = 0, creator_fee_bps = 0` (68 bytes) costs 165,520 (+16);
  - all four options with `holder = 1` (70 bytes) costs 165,533 (+29).

  The resulting LP amounts are identical in all three, and each CU value is the same in
  both images. A 60-byte instruction whose `OptionBool` byte is 2 gives
  InstructionDidNotDeserialize (102) at 6,380 CU.
- **Insufficient user balance.** A base or quote balance one token short fails inside SPL
  Token with Custom(1) (139,427 / 148,206 CU). An exact balance succeeds.

Per-case numbers: `runtime/report.json.gz` (`cases`). Full receipts, including the
instruction bytes, logs and all post-state: `runtime/receipts.jsonl.gz`.

## Reproduce

```
python3 producer.py --root <repo> --images '{"original": "<repo>/evidence/original/pump_amm/deployed.so", "candidate": "<candidate.so>"}' --out .
python3 verify.py --images '{"original": "<repo>/evidence/original/pump_amm/deployed.so", "candidate": "<candidate.so>"}'
```

`verify.py` checks both image sha256s against `runtime/report.json.gz`. It then re-runs
all 60 cases and the stripped-prefix control, and requires the receipts and the
recomputed report to be byte-identical to the packet. It exits 0 on PASS and 1 on any
difference. The producer is deterministic: two runs gave byte-identical runtime files.

## Files

- `producer.py` — case list, LiteSVM runner, stripped-prefix control, report.
- `verify.py` — independent re-run and byte comparison.
- `runtime/receipts.jsonl.gz` — one receipt per case (both images, plus the control CU).
- `runtime/report.json.gz` — summary and per-case table.
- `MANIFEST.json` — sha256 and size of every other file.
