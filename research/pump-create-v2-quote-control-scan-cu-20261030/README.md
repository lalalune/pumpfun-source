# Pump Main create_v2: quote-control lookup cost vs list size and quote position, original vs rebuild

## Problem

`create_v2` can take a non-whitelisted quote mint. To admit it, the handler
looks the mint up in the quote-control account. It does this with
`control_entry` (`programs/pump/src/quote_control/state.rs`), which reads the
raw account bytes, not the Borsh-decoded `QuoteControl`:

```
header = data[..108]  (discriminator check)
count  = u32 at offset 104
entries = data[108 .. 108 + 40·count]            (InvalidQuoteControl if short)
entries.chunks_exact(40).find(|e| e[..32] == quote_mint)   -> initial virtual quote reserves
not found -> UnsupportedQuoteMint (create_v2.rs:390, 6063)
```

`pump-create-v2-*` packets admit the quote through lists of 1–3 entries. The
sibling `pump-quote-control-list-scan-cu-20261030` measures the admin
instructions, which decode the whole Vec. This packet holds `create_v2` fixed
and varies only the list length N (1..1,000) and the position j of the quote
mint. It reads the compute units (CU) on both images.

## Cases (32)

The quote is a non-whitelisted SPL quote mint (`Global.whitelist` = another
key). The remaining accounts are: quote mint, curve quote ATA, SPL Token, and
the quote-control PDA. The other entries are `u16(i + 1) ‖ 30 × 0x4d` keys.

- N = 256 with the quote at j = 0, 1, 2, 4, 8, 16, 32, 64, 128, 255.
- N = 1, 2, 4, 8, 16, 32, 64, 128, each with the quote first and last. The two
  N = 1 rows are the same input.
- The quote absent from N = 1, 8, 64, 256.
- N = 1,000 with the quote last and first. This count is above the
  `MAX_QUOTE_CONTROL_MINTS` = 256 cap that `add_quote_control_mint` enforces.

## Method

- `producer.py` is the create_v2 harness of
  `research/pump-create-v2-quote-mint-extension-allowlist-20261030`. Only these
  parts were replaced: the case plan and a `cu_by_position` summary field.
- Each case runs under two Token-2022 configurations:
  - `mainnet-token-2022`: the repository's
    `evidence/dependencies/spl_token_2022/deployed.so`. **This is the
    configuration the tables use.**
  - `builtin-token-2022`: LiteSVM's built-in Token-2022. Every non-absent case
    stops there with `InvalidRealloc` during the token-metadata step, the same
    limitation recorded in the earlier create_v2 packets. Both images stop at
    the same place in every case.
- Pump runs under the upgradeable loader. Accounts are synthetic, keys come
  from fixed seeds, and the clock is fixed. Each case runs in a fresh VM.
  There is no network.
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

## Result

**Original and rebuild behave identically in all 32 cases, under both
configurations** (`behavior_mismatches = []`).

- Under `mainnet-token-2022` there are 28 successes and 4
  `UnsupportedQuoteMint` (6063, the absent rows).
- The count-1,000 lists are accepted: the quote is found at entry 999.
- CU is identical in 28 cases and logs are identical in 28 cases, per
  configuration.

| N | quote position j | outcome | CU orig / rebuild |
|---|---|---|---|
| 256 | 0 | success | 142,303 / 142,303 |
| 256 | 1 | success | 142,332 / 142,332 |
| 256 | 2 | success | 142,361 / 142,361 |
| 256 | 4 | success | 142,419 / 142,419 |
| 256 | 8 | success | 142,535 / 142,535 |
| 256 | 16 | success | 142,767 / 142,767 |
| 256 | 32 | success | 143,231 / 143,231 |
| 256 | 64 | success | 144,159 / 144,159 |
| 256 | 128 | success | 146,015 / 146,015 |
| 256 | 255 | success | 149,698 / 149,698 |
| 1 / 2 / 4 / 8 / 16 / 32 / 64 / 128 / 1,000 | 0 | success | 142,303 / 142,303 (all 9) |
| 2 | 1 | success | 142,332 / 142,332 |
| 4 | 3 | success | 142,390 / 142,390 |
| 8 | 7 | success | 142,506 / 142,506 |
| 16 | 15 | success | 142,738 / 142,738 |
| 32 | 31 | success | 143,202 / 143,202 |
| 64 | 63 | success | 144,130 / 144,130 |
| 128 | 127 | success | 145,986 / 145,986 |
| 1,000 | 999 | success | 171,274 / 171,274 |
| 1 | absent | UnsupportedQuoteMint | 80,720 / 80,602 |
| 8 | absent | UnsupportedQuoteMint | 80,923 / 80,805 |
| 64 | absent | UnsupportedQuoteMint | 82,547 / 82,429 |
| 256 | absent | UnsupportedQuoteMint | 88,115 / 87,997 |

Reading the table (measured values only):

- **Cost model.** Every success is exactly `142,303 + 29·j` CU on both images.
  For example, j = 999 adds 28,971 = 29 × 999.
- **List length costs nothing when the quote is first.** N from 1 to 1,000 all
  cost 142,303. Unlike the admin instructions, create_v2 does not decode the
  list.
- **An absent quote scans all N entries.** It costs 80,720 / 80,923 / 82,547 /
  88,115 for N = 1 / 8 / 64 / 256, which is exactly 29 CU per added entry.

### Compute-unit / log differences

| orig − rebuild | cases | where | differing log lines |
|---|---|---|---|
| +118 | 4 | `UnsupportedQuoteMint`, `create_v2.rs:390`, every N | AnchorError site `programs/pump/src/create_v2.rs:390` vs `src/create_v2.rs:390`, plus `consumed` |
| 0 | 28 | every success, every N and j, including N = 1,000 | none |

Cause location:

- The scan costs the same on both images: 0 on 28/28 successes.
- The +118 is constant across N. Of it, 14 CU is `len("programs/pump/")` in
  the AnchorError file string. The other 104 CU are not explained by any log
  line.
- `pump-create-v2-quote-mint-extension-allowlist` records the same +118 at
  this site.

## Limits

- SPL quote only, with one position grid. Entries differ from the quote in
  their first bytes.
- `builtin-token-2022` rows stop at `InvalidRealloc`; see Method.
- Synthetic state.

## Reproduce

```
python3 producer.py --root <repo> --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}' --out .
python3 verify.py --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}' --token-2022 <repo>/evidence/dependencies/spl_token_2022/deployed.so
```

The producer output is byte-identical across runs. verify.py first checks the
image and Token-2022 sha256 values against `runtime/report.json.gz`. It then
replays all 32 cases × 2 images × 2 configurations (128 receipts) and compares
each receipt byte for byte. Last, it recomputes the summaries. It exits 0 on
success and 1 on any difference.
