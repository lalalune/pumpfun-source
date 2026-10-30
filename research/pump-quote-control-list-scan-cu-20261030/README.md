# Pump Main quote-control list operations: cost vs list size and mint position, original vs rebuild

## Problem

`QuoteControl` (PDA `[b"quote-control"]`) holds `mints: Vec<QuoteControlMint>`,
with 40-byte entries and at most `MAX_QUOTE_CONTROL_MINTS` = 256. Three admin
instructions walk this list (`programs/pump/src/quote_control/state.rs`):

- `set_quote_control_mint_reserves` finds the mint with `iter().position`.
  If the mint is absent it fails with QuoteMintNotWhitelisted (`state.rs:113`).
- `remove_quote_control_mint` does the same, then calls `Vec::remove(index)`,
  which shifts the tail. If the mint is absent it fails with
  QuoteMintNotWhitelisted (`state.rs:99`).
- `add_quote_control_mint` scans all N entries for a duplicate
  (QuoteMintAlreadyWhitelisted, `state.rs:77`) and checks N < 256
  (QuoteMintWhitelistFull, `state.rs:82`). It then appends. Past 50 entries it
  reallocates the account by one entry.

`pump-quote-control-admin-lifecycle-20261030` measured roles, eligibility,
growth and rent, mostly on 3-entry lists. It did not vary the list size or the
mint position. This packet holds each instruction fixed and varies only those
two, then reads the compute units (CU) on both images.

## Cases (47)

All mints are `mint_key(i)` = `u16(i + 1) ‖ 30 × 0x64`, as in the lifecycle
packet. The list is exactly full-length in its account (N ≤ 49 → 2,108 bytes;
otherwise 108 + 40·N bytes) and rent-exempt.

- **set reserves (16) and remove (16).**
  - N = 256 with the mint at position j = 0, 1, 2, 4, 8, 16, 32, 64, 128, 255,
    or absent.
  - N = 1 with j = 0.
  - N = 8 and N = 64, each with j = 0 and j = N − 1.
- **add (15).**
  - Existing N = 0, 1, 2, 4, 8, 16, 32 and 49: no realloc.
  - N = 50, 64, 128 and 255: realloc +40 bytes.
  - N = 256: full.
  - N = 255 with the new mint equal to entry 254, and equal to entry 0.

## Method

- `producer.py` is the harness of
  `research/pump-quote-control-admin-lifecycle-20261030`. Only these parts were
  replaced: the case plan, a `cu_by_position` summary field and the scope text.
- Pump runs under the upgradeable loader (program + programdata, the mainnet
  layout).
- All accounts are synthetic (IDL layouts). Keys come from fixed seeds. The
  clock is fixed. Each case runs in a fresh VM. There is no network.
- `runtime/plan.json.gz` holds every case's full initial state, signer seeds
  and instruction bytes. `verify.py` replays from that file alone.
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

**Original and rebuild behave identically in all 47 cases**
(`behavior_mismatches = []`, `outcome_mismatches = []`). The compared fields
are: error, events, handler messages, inner instructions and every account's
after-state.

- Outcomes: 42 successes, 2 QuoteMintNotWhitelisted, 2
  QuoteMintAlreadyWhitelisted and 1 QuoteMintWhitelistFull.
- Account effects:
  - `add/n50-realloc` grows the account from 2,108 to 2,148 bytes, and its
    lamports go from 15,562,560 to 15,840,960.
  - `add/n49` stays at 2,108 bytes.
  - Removes leave the length unchanged: 10,348 bytes at N = 256.
- `add/n256-full` costs 38,928 / 38,914 CU. That equals the `add-257th` case
  of the lifecycle packet, which serves as a cross-check of the harness.
- CU is identical in 42 cases and logs are identical in 42 cases.

### Position in a full list (N = 256)

| position j | set_quote_control_mint_reserves CU orig / rebuild | Δ vs j=0 | remove_quote_control_mint CU orig / rebuild | Δ vs j=0 |
|---|---|---|---|---|
| 0 | 60,922 / 60,922 | +0 | 61,033 / 61,033 | +0 |
| 1 | 60,950 / 60,950 | +28 | 61,062 / 61,062 | +29 |
| 2 | 60,978 / 60,978 | +56 | 61,091 / 61,091 | +58 |
| 4 | 61,034 / 61,034 | +112 | 61,149 / 61,149 | +116 |
| 8 | 61,146 / 61,146 | +224 | 61,264 / 61,264 | +231 |
| 16 | 61,370 / 61,370 | +448 | 61,495 / 61,495 | +462 |
| 32 | 61,818 / 61,818 | +896 | 61,956 / 61,956 | +923 |
| 64 | 62,714 / 62,714 | +1792 | 62,879 / 62,879 | +1846 |
| 128 | 64,506 / 64,506 | +3584 | 64,725 / 64,725 | +3692 |
| 255 | 68,062 / 68,062 | +7140 | 68,398 / 68,398 | +7365 |
| absent | 37,104 / 37,090 (QuoteMintNotWhitelisted) | — | 37,685 / 37,671 (QuoteMintNotWhitelisted) | — |

### List size N

| N | mint position | set_quote_control_mint_reserves CU orig / rebuild | remove_quote_control_mint CU orig / rebuild |
|---|---|---|---|
| 1 | 0 | 18,094 / 18,094 | 18,175 / 18,175 |
| 8 | 0 | 19,263 / 19,263 | 19,344 / 19,344 |
| 8 | 7 | 19,459 / 19,459 | 19,547 / 19,547 |
| 64 | 0 | 28,615 / 28,615 | 28,696 / 28,696 |
| 64 | 63 | 30,379 / 30,379 | 30,523 / 30,523 |
| 256 | 0 | 60,922 / 60,922 | 61,033 / 61,033 |
| 256 | 255 | 68,062 / 68,062 | 68,398 / 68,398 |

### add_quote_control_mint vs existing entries N

| N | case | outcome | CU orig / rebuild | Δ vs previous row / entries added |
|---|---|---|---|---|
| 0 | append | ok | 18,492 / 18,492 |  |
| 1 | append | ok | 18,771 / 18,771 | +279 / 1 → 279.0 per entry |
| 2 | append | ok | 18,966 / 18,966 | +195 / 1 → 195.0 per entry |
| 4 | append | ok | 19,357 / 19,357 | +391 / 2 → 195.5 per entry |
| 8 | append | ok | 20,141 / 20,141 | +784 / 4 → 196.0 per entry |
| 16 | append | ok | 21,709 / 21,709 | +1,568 / 8 → 196.0 per entry |
| 32 | append | ok | 24,845 / 24,845 | +3,136 / 16 → 196.0 per entry |
| 49 | append | ok | 28,177 / 28,177 | +3,332 / 17 → 196.0 per entry |
| 50 | append | ok | 30,917 / 30,917 | +2,740 / 1 → 2740.0 per entry |
| 64 | append | ok | 33,663 / 33,663 | +2,746 / 14 → 196.1 per entry |
| 128 | append | ok | 46,229 / 46,229 | +12,566 / 64 → 196.3 per entry |
| 255 | append | ok | 71,271 / 71,271 | +25,042 / 127 → 197.2 per entry |
| 256 | full | error:QuoteMintWhitelistFull | 38,928 / 38,914 |  |
| 255 | duplicate-254 | error:QuoteMintAlreadyWhitelisted | 45,604 / 45,590 |  |
| 255 | duplicate-0 | error:QuoteMintAlreadyWhitelisted | 31,126 / 31,112 |  |

Reading the tables (measured values only):

- **set reserves.** In the full list, the position term is exactly 28 CU per
  entry before the hit (+7,140 at j = 255, = 28 × 255).
- **List size dominates.** At j = 0, N = 8 → 64 → 256 adds 9,352 and then
  32,307 CU. A list of 256 costs about 3.4× a list of 1 before any scan step.
- **remove** grows by 29 CU for each of the first entries. Its slope falls
  slightly as j grows (+7,365 at j = 255 against 29 × 255 = 7,395). The tail
  that `Vec::remove` shifts gets shorter as j grows; this packet does not
  separate the two terms.
- **add** costs 195–197 CU per existing entry from N = 1 up, and 279 CU for
  the first entry. The step from N = 49 to N = 50, the first realloc, costs
  2,740 CU. After the realloc, the per-entry slope returns to 196.
- **Failures are cheaper than successes on the same list.** The absent-mint
  failures at N = 256 (37,104 and 37,685) cost less than any N = 256 success.
  A duplicate at entry 0 fails at 31,126, against 45,604 for a duplicate at
  entry 254. The difference, 14,478 CU over 254 entries, is 57 CU per entry.
- **The list code costs the same on both images.** orig − rebuild is 0 on all
  42 successes: every N, every position, the realloc and the shifts.

### Compute-unit / log differences

| orig − rebuild | cases | where | differing log lines |
|---|---|---|---|
| +14 | 5 | QuoteMintNotWhitelisted `state.rs:113` (reserves) and `:99` (remove); QuoteMintAlreadyWhitelisted `:77` (×2); QuoteMintWhitelistFull `:82` | AnchorError site `programs/pump/src/quote_control/state.rs:N` (original) vs `src/quote_control/state.rs:N` (rebuild), plus `consumed` |
| 0 | 42 | every success | none |

Cause location: +14 = `len("programs/pump/")` in the AnchorError file string.
It is the same at all 4 error sites and does not depend on N or position.

## Limits

- Mints differ from each other in their first 2 bytes, so each entry compare
  stops early. Mints that share a longer prefix are not measured.
- The scan used by `create_v2` (`control_entry` in `pump_quote.rs`, which reads
  the raw account) is not run here.
- One loader (upgradeable). Synthetic state.

## Reproduce

```
python3 producer.py --root <repo> --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}' --out .
python3 verify.py --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}'
```

The producer output is byte-identical across runs. verify.py first checks both
image sha256 values against `runtime/report.json.gz`. It then replays all 47
cases × 2 images (94 receipts) and compares each receipt byte for byte. Last,
it recomputes the summary, including `cu_by_position`. It exits 0 on success
and 1 on any difference.

Files: `producer.py`, `verify.py`, `runtime/plan.json.gz`,
`runtime/receipts-upgradeable.jsonl.gz` and `runtime/report.json.gz`.
