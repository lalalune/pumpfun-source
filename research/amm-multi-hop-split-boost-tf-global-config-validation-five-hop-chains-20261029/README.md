# research: GlobalConfig validation on the split x boost x tf chain at TRUE 5 hops

## Problem

Packet #84 pinned the GlobalConfig account's own validation on the
TRUE 3-hop split chain: a wrong discriminator fails
`InvalidAccountData` (Anchor account deserialization, not the
fee-table account's 3002), a wrong owner fails 3007, lamports 0
fails 3012 while lamports 1 and 2,000,000 succeed
anchor-identically (no rent-exempt check), check order is
3012 > 3007 > `InvalidAccountData`, and key swaps split by the
swapped account's owner/existence. This packet asks whether every
one of those holds at depth 5, on the split x boost x tf chain
(three_amm + g4 + g5, final output U5 — a TRUE 5-hop route, not
the #61 shape that appended g4 only and was actually 4 hops), and
adds two things #84 did not cover: the GlobalConfig length gate
at depth 5, and a correction to a mislabeled swap case (below).

## Route and anchors

The fixture route is main -> POOL2 -> P3 -> P4 -> P5, final output
U5. Successful 5-hop swaps carry exactly 5 hop events in both
directions. Anchors (bps 100 tf, GlobalConfig unmutated):

- Buy tail 5,207,955,235,891, buyback leg 4,515,471.
- Sell payout 178,541, buyback leg 837.
- Buy-then-patched-window burn 5,254,679,949,141; sell-then-patched-window
  burn 5,338,394,848,076.
- Buy-then-sweep/collect nets: protocol 4,517,934, creator 122,160,
  collect 120,938.

## Cases (73 cases, 291 receipts, 30 parts of 10 + 1)

- **A (5 anchors):** buy, sell, buy-then-boost, sell-then-boost,
  buy-then-sweep/collect — the values above.
- **D (8):** discriminator corruption — zeroed, flipped byte,
  pool discriminator, fee-table discriminator — buy and sell.
  All fail `InvalidAccountData` with 0 events, both directions.
- **W (4):** whole-data replacement at the kept length of 949
  bytes — fee-table data, pool data, zeroed data (buy and sell).
  All fail `InvalidAccountData` with 0 events.
- **O (8):** owner faults — SPL token, Token-2022, system,
  default, Fees program — all fail 3007 with 0 events. The pump
  program itself (the true owner) succeeds anchor-identically in
  both directions, so it is a control, not a fault.
- **L (4):** lamports 0 fails 3012 with 0 events, both directions.
  Lamports 1 and 2,000,000 (below the 949-byte rent-exempt minimum)
  succeed with anchor-identical deltas: no rent-exempt check fires.
- **N (6, new):** GlobalConfig length gates at depth 5. Buy:
  100, 500, 906 bytes fail `InvalidAccountData`; 907 and 948 bytes
  succeed anchor-identically — so the buy gate is exactly 907
  bytes (the buy path reads through the buyback basis points at
  899..907 and nothing past them). Sell at 906 bytes also fails
  `InvalidAccountData`.
- **R (6):** check order at depth 5 is 3012 > 3007 >
  `InvalidAccountData`, both directions: disc+owner fails 3007,
  lamports-0+disc fails 3012, lamports-0+owner fails 3012, all
  three together fail 3012, flipped-disc+system-owner sell fails
  3007.
- **S (9):** key swaps at multi-hop metas index 3 (the
  GlobalConfig slot). Fee-table key fails 3007 (its owner is the
  Fees program); pool key fails `InvalidAccountData` (its owner
  is the pump program, so the owner gate passes and deserialization
  fails); user quote account fails 3007 (SPL token owner); Fees
  program key fails 3007; the PLAIN key fails 3007; the truly
  absent key fails 3012 — buy and sell alike.
- **P (8):** leg parity. Disc-zero fails `InvalidAccountData`
  on the v2 buy, v2 sell, legacy buy, legacy sell, the stable buy,
  the patched-window boost, and the protocol sweep. Owner-token
  fails 3007 on the v2 buy.
- **M (4):** mid-chain corruption. A good buy, then a corruption
  patch, then a second buy fails `InvalidAccountData` (disc),
  3007 (owner), 3012 (lamports) respectively. After corruption,
  both sweeps fail `InvalidAccountData`, and collect stays a
  silent 0-event no-op even though the good buy filled the
  creator bucket — collect only moves what a sweep already moved.
- **F (4):** downstream legs after a failed buy split by whether
  they read GlobalConfig. Both sweeps fail `InvalidAccountData`,
  collect is a silent no-op, and the patched-window boost fails
  `InvalidAccountData`. But the token claim still pays the full
  seeded 3,334,551 and the plain-quote cashback claim still pays
  the full 5,475: neither claim leg reads GlobalConfig, so a
  corrupted config does not gate claims.
- **S2 (3):** setters under a corrupted GlobalConfig. The control
  buyback-config setter succeeds; disc-zero fails
  `InvalidAccountData` on both the buyback-config setter and the
  disable setter.
- **T (4):** tf variants — disc-zero at tf5000 and tf0, owner-token
  at tf5000, fee-table-key swap at tf0 — fail with the same codes
  as at bps 100: validation is tf-neutral.

## Result

Every #84 finding reproduces exactly at depth 5, with one
correction and one new gate:

1. **Correction — the "fresh key" was never fresh.** The #137
   builder's `FRESH` constant is `Pubkey.from_bytes(bytes([77]) *
   32)`, which is exactly the fixture's `PLAIN` key: setup sets
   that account as a Token-2022 token account with 2,157,600
   lamports. So #137's "absent fresh key → 3007" cases actually
   measured a present, Token-2022-owned account. This packet
   relabels those swaps as the PLAIN key (3007, both directions)
   and re-measures a truly absent key, bytes `[123] * 32`, which
   fails 3012 in both directions — matching #84 and matching the
   check order (an absent account has 0 lamports, so the
   lamports gate fires before the owner gate). #137's submitted
   packet keeps its old label; the measurement here supersedes it.
2. **New gate — 907 bytes.** The buy path needs exactly 907
   bytes of GlobalConfig and nothing more (948 also succeeds
   anchor-identically); 906 fails. The sell path also fails at
   906.
3. **Ghost counts.** Unlike the fee-table length gate's 6082
   failure (4 buy ghosts at depth 5, packet #136), every
   GlobalConfig validation failure here is 0 events in both
   directions: the checks fire before any hop executes, so no
   hop event is ever emitted on a failed trade.

Across the original, control, and candidate images, all 73 cases
agree: 0 divergent cases.

## Limits

- GlobalConfig mutations (`cfg_valid`, `cfg_len`) and mid-case
  `cpatch` resets are harness fixture edits recorded with empty
  transactions, not on-chain instructions; they exist to place the
  account in the corrupted state the program then validates.
- Results are LiteSVM executions of the original, control, and
  candidate program images on this fixture; they pin the observed
  gate codes, ghost counts, tails, and rollback behaviour, and
  make no claim about any other account shape or program path.
- No source change is proposed.

## Files

- `README.md` — this file.
- `producer.py` — the packet builder (case list, harness edits,
  receipt writer).
- `verify.py` — independent re-verification: signatures, deltas,
  withheld, lamports, events, error codes, rollback, fixture
  pool/config/UVA/GVA/mint fields, account lengths, and the
  headline pins above. Run it from this directory.
- `MANIFEST.json` — sha256 and byte counts for every packet file.
- `runtime/report.json.gz` — per-case, per-image summaries.
- `runtime/raw-transactions-part01..30.jsonl.gz` — the 291
  receipts, 10 per part (last part 1).

Verify: `python3 verify.py` prints
`PASS: 73 cases, 291 receipts, 30 parts, ...` (full line in the
script).

Made via @slopdotcash
