# research: multi-hop split x boost x tf chains with mayhem/cashback-flagged hop pools

## Problem

On the same true-3-hop split x boost x tf chain as packets #64-#108
(`three_amm` only, final output U3, tf100 unless noted), this packet
measures what happens when the hop pools themselves carry mayhem /
cashback mode flags: boost on a flagged pool, boost before / after a
mode-gated trade, global mode toggles mid-walk between boost and
trade, and sweep / collect / claim after a mode-gated failed leg.

Pool flags are set by patching pool bytes 243 (mayhem) / 244
(cashback); global flags by patching GlobalConfig bytes 417
(mayhem) / 642 (cashback). The first trade of a case costs the payer
1,849,400 lamports when it auto-creates the user volume accumulator
(fee 5,000 + rent 1,844,400); cases with a seeded UVA cost 5,000.
All amounts are for this fixture.

## Cases

66 cases, 447 receipts (66 cases x steps x 3 images), 45 parts
of 10 receipts (44x10 + 7). Control == candidate in every case;
original differs from both in exactly 32 cases, all in the mode-gate
map (see Result).

- A (5): anchors. Multi-hop buy tail 5,262,910,281,902; multi-hop
  sell payout 178,541; boost anchor burn 5,338,379,201,831 (VQ
  patched to 10^9); buy then VQ-patch then boost burn
  5,254,679,949,141; boost then buy tail 5,139,964,404,268.
- B (14): flagged-hop trades. Buy: main / p2 / p3 x cb / mayhem /
  both (9). Sell: main cb / mayhem / both, p2 both, p3 both (5).
- C (11): flagged trade then boost (7: buy cb / mayhem / both on
  main, both on p2, both on p3; sell cb on main, cb on p3), and
  boost then flagged trade (4: main cb / both, p2 both, p3
  mayhem).
- D (7): boost on a flagged pool itself: main cb / mayhem / both,
  main cb twice, and boost3 on the p3 tail pool cb / mayhem /
  both.
- E (6): global toggles mid-walk: global mayhem off, global
  cashback off, both off, boost then global mayhem off, boost
  then global cashback off, mayhem off then on again.
- F (6): after a mode-gated failed leg: flag cleared then fresh
  buy + boost; mayhem cleared then sell; buy fail then protocol
  sweep + creator sweep + boost; both fail then creator sweep +
  collect + boost; buy fail then token claim + boost; p3 both
  fail then protocol sweep + creator sweep.
- G (4): liquidity on a flagged pool: cb deposit, mayhem deposit,
  both withdraw, cb deposit then boost.
- H (3): plain-quote cashback claims (no withdraw-withheld
  authority patched onto the plain mint): failed buy then claim,
  failed plain boost then claim, mayhem-flagged buy then claim
  with a seeded UVA.
- I (3): flagged buys at tf0 / tf5000 then boost: main cb tf0,
  main cb tf5000, main both tf5000.
- J (7): multi-flag chains: main cb + p2 mayhem, main mayhem +
  p2 cb, main both + p2 both, p2 cb + p3 mayhem, main cb + p3
  mayhem, main cb + p2 mayhem then boost, main mayhem + p2 cb
  then boost.

## Result

### The mode-gate map (the 32 divergences)

Original and rebuild gate differently, and the difference is fully
determined by hop position, direction, and flag combination:

- Original: the mayhem gate fires on every hop; the cashback gate
  fires ONLY on the terminal (p3) hop. At p3, cashback takes
  priority over mayhem, so a p3 both-flagged hop fails 6079, not
  6080.
- Rebuild: the cashback gate fires on every hop, with priority
  over mayhem everywhere, so any cb- or both-flagged hop fails
  6079.
- Ghost events equal the hops executed before the failing hop.
  Buy runs main -> p2 -> p3; sell runs p3 -> p2 -> main.
  Examples: p2 cb buy fails 6079 with 1 ghost on the rebuild
  (original passes); p3 cb buy fails 6079 with 2 ghosts on both
  images; main cb sell passes on the original and fails 6079
  with 2 ghosts on the rebuild (main is last in sell); p3 both
  sell fails 6079 with 0 ghosts on both images (p3 is first in
  sell); main mayhem masks p2 cb, failing 6080 with 0 ghosts on
  both images (not divergent).

Every non-divergent case agrees byte-for-byte across all three
images, and every divergent case agrees between control and
candidate: the divergence is original-vs-rebuild only.

### Boost is mode-blind

- Boost on a cb-, mayhem-, or both-flagged main pool burns
  exactly the anchor 5,338,379,201,831; a second boost on the
  cb-flagged pool burns 5,254,441,549,265 (the #100 decay-ladder
  second value).
- Boost after a failed leg burns the anchor (failed cb buy then
  boost: 5,338,379,201,831 on the rebuild; failed chain then
  boost: 5,338,379,201,831 on both images). Boost after a
  successful leg burns the post-buy value 5,254,679,949,141.
  Boost before a gated trade does not change which gate fires:
  boost then main cb buy still passes on the original (tail
  5,139,964,404,268) and still fails 6079 on the rebuild.
- Boost3 on a flagged tail pool fails 6065 on all images (the
  boost window is 0 on a fresh tail pool, flag or not).
- Global toggles do not rescue pool flags: with global mayhem
  and cashback both off, a both-flagged buy still fails 6080 on
  the original and 6079 on the rebuild; boost then global
  cashback off still leaves a p2 cb buy passing on the original
  (tail 5,139,964,404,268) and failing 6079 on the rebuild; a
  mayhem off-then-on round trip restores 6080.
- A failed leg leaves no residue: with the flag cleared, the
  rebuild's fresh buy tails 5,262,910,281,902 and its following
  boost burns 5,254,679,949,141, while the original's second buy
  (its first buy had already succeeded) tails 5,072,980,706,277
  with a following boost of 5,172,933,848,347 -- a clean second
  leg, not a residue effect; with mayhem cleared, a sell pays
  the anchor 178,541.

### Sweeps, collects, and claims after a failed leg move the next burn through the real quote vault

The cpatch resets the pool VQ field to 10^9 in both walks, so the
burn differences below come from the real quote vault, not the VQ
field:

- Original buy then protocol + creator sweep then boost burns
  5,254,875,541,549 (post-buy value + 195,592,408 for 4,686,964
  swept, about 41.73 per unit at the post-buy evaluation point,
  cf. #102's -41.69 trade secant). The sweep pays the buy
  accrual 4,563,570 (protocol net 4,517,934 + withheld 45,636).
- Rebuild failed buy then fixture-only sweeps then boost burns
  5,338,384,580,607 (anchor + 5,378,776 for 125,882 swept).
- Failed both buy then creator sweep + collect then boost burns
  5,338,384,474,298 on both images (anchor + 5,272,467 for
  123,394 swept, about 42.73 per unit, the #100 slope). Collect
  nets 120,938 + withheld 1,222.
- A token claim pays the full 3,334,551 regardless of buy success
  when the UVA is seeded, and the following boost is the
  post-buy value on the original and the anchor on the rebuild.
- After a p3 both-flagged failure, a protocol sweep fails 6013
  while a creator sweep pays the fixture 123,394 in full to the
  creator ATA (no withheld split on this plain sweep).

### Liquidity and plain-quote claims on flagged pools

- Deposit and withdraw on flagged pools are mode-blind and
  identical on all images: deposit userbase -160,619,896,
  userquote -29,610, LP +1,000,000; withdraw userbase
  +160,619,895, userquote +29,018, LP -1,000,000. Deposit then
  boost on a cb pool burns 5,338,379,222,079 (anchor + 20,248).
- Plain-quote cashback claim pays 5,475 when a UVA exists: after
  a successful plain buy (which auto-creates it), and after a
  failed buy when the UVA was seeded. After a failed buy with no
  seeded UVA, the claim fails 3012 (no UVA was ever created).
  A plain boost fails IncorrectProgramId (#103) and the
  following claim fails 3012 on both images.
- The tf variants keep the same gate map: main cb tf0 buy tails
  5,315,084,721,958 on the original (the plain tail, no fee) with
  a following boost of 5,306,492,329,463, while the rebuild's
  failed buy is followed by the tf0 anchor boost
  5,391,870,655,895; main cb tf5000 buy tails 2,682,425,360,738
  with a following boost of 2,685,165,599,125, while the
  rebuild's failed buy is followed by the tf5000 anchor boost
  2,706,767,012,738; main both tf5000 fails 6080 on the original
  and 6079 on the rebuild, with both boosts at the tf5000
  anchor.

## Limits

- Amounts are fixture-specific (fee table, pool reserves, tf100
  unless noted). The gate codes 6079 (cashback) / 6080 (mayhem)
  are observed from the three images only; the mayhem program
  source is not in the sparse checkout, so this packet makes no
  claim about the intended gate design, only the observed gate
  behaviour.
- `cpatch` steps are harness field resets (empty transactions),
  never instructions; they carry the flag patches and VQ resets
  between legs.
- No source-change proposal is made, and no full-program
  equivalence is claimed: the 32 original-vs-rebuild gate
  divergences above are the finding.

Made via @slopdotcash
