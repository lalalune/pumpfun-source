# research: split x boost x tf mode-hop gates at TRUE 5 hops

3rd-run packet #119: the split x boost x tf chain at TRUE 5 hops
(`three_amm` + g4 + g5, final output U5) meets mayhem/cashback-flagged
hop pools. This is the 5-hop extension of #109 (the 3-hop mode-gate
map), not a re-measure: #109 pinned, at 3 hops, that the original
gates cashback only on the terminal hop while the rebuild gates it on
every hop, that mayhem gates on every hop on both images, and that on
a both-flagged hop the original fires mayhem 6080 first while the
rebuild fires cashback 6079 first. The open question was whether that
split survives at depth 5 — does the original's terminal-only rule
move to P5, do ghost-event counts scale with hop position, and does
the both-flag priority rule hold at every non-terminal hop?

Route confirmation (from the builder itself): the fixture route calls
`three_amm` and appends the g4 and g5 hop groups — 5 hop groups,
final output U5. This packet does not repeat 3rd #61's naming error
(a "3-hop" packet whose builder actually appended a P4 group): the
name, the README and the route all say 5 hops.

## Problem

On a 5-hop route, which hop's flag actually stops the chain, and on
which image? Two orderings are at stake: the cashback gate's hop
scope (original terminal-only vs rebuild every-hop) and the
mayhem-vs-cashback priority on a both-flagged hop. A third question
is the ghost count: when a hop rejects, how many earlier hop events
have already been emitted, and does that count track hop position
in both directions (buy runs main -> P2 -> P3 -> P4 -> P5, sell runs
P5 -> P4 -> P3 -> P2 -> main)? Finally, does any of this move the
boost leg — does a boost on a flagged pool, or after a mode-gated
failure, burn anything other than the anchor?

## Cases

57 cases, 321 receipts (107 steps x 3 images), 33 parts (32x10 + 1).
All cases run the same steps on the original, control (#424) and
candidate (#427) images. All families run under tf100 on the quote
mint unless noted. Pool flags are pool bytes 243 (mayhem) / 244
(cashback), applied per case; global flags are GlobalConfig bytes
417 (mayhem) / 642 (cashback), toggled with the real toggle
instructions mid-walk.

- A anchors (5): 5-hop buy, 5-hop sell, patched-window boost,
  buy-then-boost, boost-then-buy.
- B buy direction, one flag position at a time (15): each of main,
  P2, P3, P4, P5 flagged cashback, mayhem, or both, then a buy.
- B2 sell direction (7): main cashback / both, P2 both, P3 both,
  P4 both, P5 cashback / both, then a sell.
- C flagged leg, then boost (6): main-cashback buy then boost,
  P4-both buy then boost, P5-both buy then boost, main-cashback
  sell then boost, P5-cashback sell then boost, boost then
  P4-both buy.
- D boost on a flagged pool itself (4): main cashback, mayhem,
  both, and cashback twice.
- E global toggles mid-walk (3): mayhem off then cashback buy
  then boost; cashback off then cashback buy then boost; both
  off then both buy.
- F failed leg, then downstream legs (4): cashback fail, clear
  the flag, buy, boost; mayhem fail, clear, sell; cashback fail,
  protocol + creator sweep, boost; P5-both fail, P5 protocol +
  creator sweep.
- G flagged pool, liquidity legs (2): cashback-pool deposit,
  both-pool withdraw.
- H plain-quote cashback claims beside flagged legs (2, no_ww):
  cashback fail then claim; cashback fail then seeded-UVA claim.
- I tf variants (3): cashback buy at tf0 then boost; cashback
  buy at tf5000 then boost; P5-both buy at tf5000 then boost.
- J multi-flag combos (6): main-cashback + P4-mayhem buy;
  main-mayhem + P4-cashback buy; P2-cashback + P5-mayhem buy;
  P4-cashback + P5-mayhem buy; main-cashback + P5-mayhem buy;
  P4-both + P5-both buy.

## Result

31 of 57 cases diverge original-vs-rebuild, all of them mode-gate
cases (the full list is asserted in verify.py). Control == candidate
everywhere. The #109 split scales exactly with hop position: the
terminal hop moved from P3 to P5, and nothing else changed.

### Anchors (family A)

- 5-hop buy tail U5 5,207,955,235,891 (buyback leg 4,515,471 +
  withheld 45,611; per-hop vault deltas main -> P5:
  5,332,264,170,203 / 5,303,981,938,022 / 5,275,998,139,846 /
  5,248,308,076,854 / 5,207,955,235,891). The tf0/plain tail is
  5,259,040,470,738 — exactly #62's 5-hop tail.
- 5-hop sell payout 178,541 (leg 837 + withheld 9), 5 hop events.
- Patched-window main boost burn 5,338,379,201,831 (the #109
  anchor); buy-then-boost 5,254,679,949,141; boost-then-buy tail
  5,087,534,167,771.

### Buy direction: original terminal-only, rebuild every-hop (family B)

- Cashback, original: every non-terminal hop passes at full tail
  (main, P2, P3, P4 all 5,207,955,235,891, 5 events); only the
  terminal P5 hop fails, 6079 with 4 ghosts.
- Cashback, rebuild: 6079 at every hop, with ghost count exactly
  the hops executed before the failing hop — main 0, P2 1, P3 2,
  P4 3, P5 4.
- Mayhem, both images: 6080 at every hop with the same ghost
  ladder — main 0, P2 1, P3 2, P4 3, P5 4. Mayhem is hop-scope
  identical on original and rebuild, so no mayhem-only case
  diverges.
- Both-flagged, original: mayhem first — 6080 at every
  non-terminal hop (same ghost ladder), and 6079 at the terminal
  P5 hop (cashback priority at the terminal hop, 4 ghosts).
- Both-flagged, rebuild: cashback first — 6079 at every hop with
  the same ghost ladder. So every non-terminal both case
  diverges (6080 vs 6079) and the terminal both case agrees
  (6079 vs 6079).

### Sell direction: the mirror image (family B2)

Sell runs P5 -> P4 -> P3 -> P2 -> main, so the ghost ladder
reverses: P5 is first (0 ghosts), main is last (4 ghosts).

- Cashback, original: passes everywhere except the terminal
  main hop — main-cashback sell succeeds at payout 178,541
  (5 events); P5-cashback sell fails 6079 with 0 ghosts.
- Cashback, rebuild: 6079 at every hop; main-cashback sell
  fails with 4 ghosts.
- Both-flagged, original: 6080 at every non-tail hop, and 6079
  at the tail P5 hop with 0 ghosts (first in sell order) —
  cashback priority at the tail hop, exactly as in buys; the
  tail hop is P5 in both directions, only the execution order
  differs. Main-both sell is 6080 original vs 6079 rebuild with
  4 ghosts.
  Both-flagged, rebuild: 6079 at every hop with the mirrored
  ghost ladder (P4 1, P3 2, P2 3, main 4).

### Boost is mode-blind at depth 5 (families C, D)

- A boost on a cashback, mayhem, or both-flagged main pool burns
  exactly the anchor 5,338,379,201,831; a second boost on a
  cashback pool burns the decay value 5,254,441,549,265.
- After a failed leg, the boost burns the value matching what
  actually executed: original cashback-buy then boost =
  post-buy 5,254,679,949,141, rebuild failed-buy then boost =
  anchor 5,338,379,201,831; original cashback-sell then boost =
  post-sell 5,338,394,848,076, rebuild failed-sell then boost =
  anchor; failed terminal P5-both buy then boost = anchor on
  both images.
- Boost-then-P4-both-buy still diverges (original 6080 with 3
  ghosts, rebuild 6079 with 3 ghosts): the boost does not change
  which gate fires.

### Global toggles do not rescue pool flags (family E)

Turning mayhem off, cashback off, or both off globally leaves the
pool-flag gates untouched: main-cashback buy still passes on
original and fails 6079 on rebuild, and main-both buy still fails
6080 original / 6079 rebuild. The following boosts are the
post-buy / anchor values respectively.

### Failed legs leave no residue (family F)

- Cashback fail, clear the flag, buy again: original second-buy
  tail 4,918,089,082,874 then boost 5,172,933,848,347; rebuild
  fresh-buy tail 5,207,955,235,891 then boost 5,254,679,949,141.
- Mayhem fail, clear, sell: payout 178,541 on both images.
- Cashback fail then protocol + creator sweep then boost:
  original 5,254,875,541,549, rebuild 5,338,384,580,607 — the
  same fixture-sweep values as #109, so sweeps move the next
  burn through the real quote vault at depth 5 exactly as at
  depth 3.
- P5-both fail then P5 protocol sweep fails 6013 (as #109's P3
  case), then the P5 creator sweep pays the fixture 123,394 in
  full on both images.

### Liquidity and claims are mode-blind (families G, H)

- Cashback-pool deposit mints 1,000,000 LP; both-pool withdraw
  burns 1,000,000 LP — identical on all images, as at depth 3.
- Plain-quote cashback claim after a failed buy pays 5475 on
  original (auto-created UVA) and fails 3012 on rebuild (no
  UVA); with a seeded UVA it pays 5475 on both images even
  after the failed buy.

### Tf variants keep the same gate map (family I)

- Cashback buy at tf0 then boost: original 5,306,492,329,463,
  rebuild failed-buy then boost = tf0 anchor 5,391,870,655,895.
- Cashback buy at tf5000: tail 2,668,075,748,732, then boost
  2,685,165,599,125 (original); rebuild failed-buy then boost =
  tf5000 anchor 2,706,767,012,738.
- Failed terminal P5-both buy at tf5000 then boost = tf5000
  anchor 2,706,767,012,738 on both images.

### Multi-flag chains confirm hop order at depth 5 (family J)

- Main-mayhem masks P4-cashback: 6080 on both images, 0 ghosts,
  not divergent — the earliest failing hop in buy order decides.
- Main-cashback + P4-mayhem: original 6080 (3 ghosts — the
  mayhem hop is reached after main, P2, P3), rebuild 6079
  (0 ghosts — the cashback hop fires first).
- P2-cashback + P5-mayhem: original 6080 with 4 ghosts, rebuild
  6079 with 1 ghost.
- P4-cashback + P5-mayhem: original 6080 with 4 ghosts, rebuild
  6079 with 3 ghosts.
- Main-cashback + P5-mayhem: original 6080 with 4 ghosts,
  rebuild 6079 with 0 ghosts.
- P4-both + P5-both: original 6080 with 3 ghosts (first both
  hop in buy order), rebuild 6079 with 3 ghosts (first cashback
  hop) — same ghost count, different code.

## Limits

- LiteSVM harness only; no mainnet or devnet execution.
- The fixture split chain is the 3rd #64/#71/#109 fixture at 5
  hops (tf100); the gate map is pinned for that fixture state,
  not claimed for other pool states.
- The mayhem multi-hop gate (6080) is measured with the flagged
  pool at each hop position; a mayhem-flagged pool combined
  with a disable bit was not measured here (see #114 for the
  disable-vs-mode priority at 3 hops).
- The packet pins behaviour; it makes no claim about source
  changes, builds, or whole-program identity. Error sites are
  recorded per image and are not compared across images.

Made via @slopdotcash
