# Pump Fees: social-fee PDA lifecycle, rate-limit window and claim v1/v2 sequences

## Problem

`scripts/fees_social_create_differential.py`,
`fees_social_claim_differential.py` and `fees_social_claim_v2_differential.py`
run each `create_social_fee_pda` / `claim_social_fee_pda` /
`claim_social_fee_pda_v2` call once, on a SocialFeePda written directly into
a fresh LiteSVM. So none of them checks what a later claim sees after an
earlier create, deposit, claim, setter or clock move. They also do not compare
`Program log:` text. That text is where a rate-limited or empty claim shows
up, because those claims succeed (see Result).

This packet runs **chains** of transactions on one persistent LiteSVM per image:
original `evidence/original/pump_fees/deployed.so` and the rebuilt
candidate. The SocialFeePda is created by the program itself, funded by System
Program transfers, and claimed repeatedly while the clock, the global rate
limit, the social claim authority and `disable_flags` change. Every step is
compared between the two images.

Images (sha256, recorded in `runtime/report.json.gz`):

- original `4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e`
- candidate `7a14f41440c60ac6e95053e9fdc712376a1eac3447ec2de6fa29b1b6ec654900`

## Cases

55 cases, 298 transactions, each run on both images. The transactions hold
237 Pump Fees instructions, 77 System Program transfers and 13 compute-budget
instructions (one per v2 claim). 14 transactions carry two or more non-budget
instructions. Signers come from fixed seeds (223 to 226). Clock starts at unix
1,700,000,000 (`t`), and individual steps set other values. Initial state is
one synthetic FeeProgramGlobal (authority AUTH, social claim authority AUTH
unless stated, `claim_rate_limit` 60 unless stated, flags 0). Users: U1 =
(`"12345"`, platform 0), U2 = (`"12345"`, platform 1), U3 = (`"67890"`,
platform 0). Claims pay to THIRD unless stated. Deposits are 1,000,000
lamports unless stated.

- `l-*` (10): lifecycle. Claim before create, create then empty claims, the
  60 s window at +0/+59/+60/+61/+120/+121/+122, accumulation of
  `total_claimed`, whether an empty claim starts the window, whether a
  rate-limited claim moves `last_claimed`, create twice / after a claim,
  create on an address prefunded with 5,000,000 or 1 lamport, and a
  1-lamport deposit.
- `p-*` (3): independence of U1/U2 (same user id, different platform) and
  U1/U3, including two claims and three creates in one transaction.
- `t-*` (5): same-transaction ordering: create+fund+claim, fund+claim,
  claim+fund, claim+claim, and claim to the fee payer + fund.
- `a-*` (8): social claim authority transitions. Rotation AUTH→OTHER between
  claims and inside one transaction (both orders, old/new signer), global
  `set_authority` AUTH→OTHER, social authority THIRD distinct from the admin,
  social authority set to the zero key and back, authority as recipient.
- `r-*` (7): global `claim_rate_limit` changed between claims (0, 1, 1000,
  u64 max, and back to 60), u64 max and 2^63 present from the start.
- `c-*` (6): clock moves. Backwards by 100 s, claims at unix -5 / -1 / 0,
  and later clocks up to 2^62.
- `f-*` (8): `disable_flags` set to 1, 2, 4, 8, 16, 128 between create/claim
  steps and cleared again, and 255 set inside a claim transaction (before
  and after the claim).
- `v-*` (8): v1 (`claim_social_fee_pda`, lamports) and v2
  (`claim_social_fee_pda_v2`) on the same PDA. The v2 claims use USDC
  (`EPjFWdd5…`, PDA ATA holding 5,000,000 or 0 units) or WSOL (PDA ATA
  holding 3,000,000). Cases: v2 twice across the window, v1 then v2 and v2
  then v1 in the same second, v1+v2 in one transaction, v2 after rotating
  the social authority, v2 under flag 2.

Compared per step: transaction error, Anchor error code and number, return
data, `Program data:` events, `Program log:` lines, and lamports/owner/length/
sha256 of the watched accounts: global, the three social PDAs, AUTH, OTHER,
THIRD, PAYER, and in `v-*` the PDA's and THIRD's token accounts. Each step
also records a decode of the SocialFeePda fields and of the SPL token amount.
Final lamports and bytes of the watched accounts are compared too. Compute
units are recorded but not part of the match.

## Result

**All 55 cases match on every compared field. No case diverges.** The
per-step outcome lists are equal, and compute units are equal in all 298
steps. No step logs a panic. Outcome totals over 298 steps (original =
candidate): ok 284, `NotAuthorized` (6016) 8, `FeatureDeactivated` (6021) 5,
`AccountNotInitialized` (3012) 1.

The behaviors measured below are the same on both images.

### Rate-limited and empty claims succeed without doing anything

- A claim inside the rate-limit window does **not** fail. The transaction
  succeeds, logs `Claim rate limit exceeded`, emits no event, and changes no
  account other than the fee payer's fee. 33 steps took this path. A claim
  with nothing above rent also succeeds, logs `No fees available to claim`,
  and emits no event (11 steps). By contrast, `sweep_buyback` returns
  `ClaimRateLimitExceeded` (6027) as an error (measured in PR #1907).
- Because these claims succeed, they do not roll back their transaction.
  `claim + claim` in one transaction succeeds: the first claim moves
  1,000,000 lamports and the second is a no-op. `v1 + v2 usdc` in one
  transaction moves only the v1 lamports, and the v2 half logs
  `Claim rate limit exceeded`.
- A second `create_social_fee_pda` on an existing PDA also succeeds. It logs
  `social_fee_pda already exists`, emits no event and does not change the
  account, also after a claim and with a different payer (7 steps).

### Rate-limit window (global `claim_rate_limit` = 60)

- After a claim at `t`, claims at +0 and +59 are no-ops and the claim at +60
  pays. So the window ends at exactly `last_claimed + 60`. Then +61 is a
  no-op, +120 pays and +121/+122 are no-ops (`l-rate-window-60`).
  `last_claimed` becomes the clock of the paying claim (1,700,000,060,
  1,700,000,120).
- No-op claims do not move `last_claimed`. A rate-limited claim at +10 leaves
  it at `t`, and the claim at +61 then pays. An empty claim leaves it at 0, so
  a deposit and a claim at +30 pay at once, and the window then runs from +30.
- `total_claimed` adds each payout: deposits 1, 2,000,000 and 3,000,000 give
  1, 2,000,001 and 5,000,001. A 1-lamport deposit is claimable (payout 1).
  The PDA is left at 2,136,720 lamports after every paying v1 claim, and that
  is also its balance right after create.
- The window is per PDA. U1 and U2 (same user id, platforms 0 and 1) and
  U1/U3 both pay in the same second, in separate transactions or in one.
- The rate is read at claim time. With rate 0 (set after a claim), a second
  claim in the same second pays. Rate 1: +1 pays. Rate 1000: +61 is a no-op,
  +1000 pays. With rate u64 max, a claim at +10 is a no-op and +10^9 is too.
  Resetting the rate to 60 lets the claim at +61 pay.
- `last_claimed` = 0 is not rate-limited. The first claim pays with rate u64
  max or 2^63 from the start. A claim at clock 0 stores `last_claimed` 0, so
  a second claim at clock 0 and a third at clock 10 also pay. Only after the
  claim at 10 (`last_claimed` 10) is the claim at 20 a no-op.

### Clock edge values

- A claim with the clock at unix -5 pays and stores `last_claimed`
  18,446,744,073,709,551,611 (2^64 - 5). After that, claims at
  1,700,000,000, at 2^62 and at 55 are no-ops. A claim at unix -1 pays and
  stores 18,446,744,073,709,551,615. Setting the rate to 0 lets a claim at
  unix 100 pay (`last_claimed` 100).
- With the clock moved back by 100 s after a claim, the claim at `t-100` is a
  no-op, and the next claim at `t+61` pays.

### Create on a prefunded address

- `create_social_fee_pda` on an address that already holds 5,000,000 lamports
  succeeds, emits its event and leaves the PDA at 5,000,000 lamports. The
  first claim pays 2,863,280 (= 5,000,000 - 2,136,720), so the prefund
  becomes claimable. With a 1-lamport prefund, the PDA ends at 2,136,720
  lamports after create.

### Social claim authority (both v1 and v2)

- After `set_social_claim_authority` AUTH→OTHER, AUTH gets `NotAuthorized`
  (6016) on claim (v1 and v2) and OTHER pays. In one transaction, rotate +
  OTHER claim pays. Rotate + AUTH claim fails, and the rotation is rolled
  back (AUTH then pays). AUTH claim + rotate pays, and OTHER pays at +61.
- The global `authority` is not the claim authority. After `set_authority`
  AUTH→OTHER, OTHER gets `NotAuthorized` on claim and AUTH (still the social
  claim authority) pays. With the social claim authority THIRD from the
  start, AUTH (admin) gets `NotAuthorized`, THIRD pays, and THIRD gets
  `NotAuthorized` on `set_claim_rate_limit`.
- Social claim authority set to the zero key: AUTH gets `NotAuthorized`.
  Setting it back to AUTH restores the claim. The authority can also be the
  recipient.

### `disable_flags`

- Bit 1 (`flags 1`) blocks `create_social_fee_pda` with `FeatureDeactivated`
  (6021, log `CreateSocialFeePda is currently disabled`). Claims still pay.
- Bit 2 (`flags 2`) blocks v1 claims and v2 USDC claims with
  `FeatureDeactivated` (log `ClaimSocialFeePda is currently disabled` in both
  cases). Create still works.
- Flags 4, 8, 16 and 128 block neither create nor claim.
- Flags 255 set in the same transaction before a claim fails the
  transaction, and the flag change is rolled back (the next claim pays).
  Claim then flags 255 pays, and the next claim at +61 fails with 6021.

### v1 and v2 on the same PDA

- v1 and v2 share one `last_claimed` window. A v2 USDC claim at `t` makes a
  v1 claim in the same second a no-op, and v1 pays at +60. A v1 claim at `t`
  makes a v2 USDC claim in the same second a no-op, and v2 pays at +60.
- v2 USDC moves the PDA ATA balance (5,000,000) to THIRD's ATA. It adds
  5,000,000 to `total_stable_claimed` and leaves `total_claimed` and the PDA
  lamports alone. v2 twice: +59 is a no-op, and +60 logs
  `No fees available to claim`.
- v2 with WSOL as the quote mint pays the PDA's **lamports** (1,000,000). It
  adds them to `total_claimed`, and the PDA's WSOL token account stays at
  3,000,000 units / 5,039,280 lamports. A v1 claim in the same second is
  then a no-op, and v1 pays at +60 (`total_claimed` 2,000,000).
- An empty v2 USDC claim (ATA balance 0) logs `No fees available to claim`
  and does not start the window. A v1 claim in the same second pays.

## Reproduce

```
python3 producer.py --root <repo> --images '{"original": "<repo>/evidence/original/pump_fees/deployed.so", "candidate": "<candidate.so>"}' --out .
python3 verify.py --images '{"original": "...", "candidate": "..."}'
```

`producer.py` is deterministic: two runs give byte-identical
`runtime/receipts.jsonl.gz` and `runtime/report.json.gz`. It derives the
Anchor discriminators locally and checks them, plus the account order and
signer/writable flags of the create, claim and claim-v2 instructions,
against `evidence/upstream/pump_fees.json` under `--root`. `verify.py` uses
only the packet files and the two images. It checks the image sha256 values
against the report and re-derives the three PDA addresses. It then replays
every case on each image and requires each step's result and the final
account state to equal the receipt. Last, it recomputes the match flags,
outcome lists, compute-unit lists and the mismatched-case list. `--images`
also accepts a path to a file containing the JSON object. Both negative
checks were run: swapped images and a receipt with one lamport value changed
each make it exit 1.

## Limits

- All state is synthetic. FeeProgramGlobal, mints and token accounts are
  written directly, and SocialFeePda accounts are made by
  `create_social_fee_pda`. No captured mainnet account was used.
- Token and ATA programs are LiteSVM's built-in SPL Token / Associated Token
  programs, not the captured dependency binaries. Only legacy SPL Token
  mints (USDC, WSOL) were used in v2. Token-2022 was not used.
- The rate-limit rules above are stated as measured inputs and outputs. The
  packet does not derive the comparison from the binary. Negative and zero
  clock values cannot occur on a live cluster in normal operation, and they
  are included only as boundary inputs.
- Recipients are system-owned wallets (THIRD, PAYER, AUTH). v2 destination
  ATAs exist before the claim, so the create-destination path is not
  measured.
- This packet contains no source change and no claim about any program other
  than the measured behavior above.
