# Pool account validation on the split x boost x tf chain (true 3 hops)

## Problem

Packets 3rd #83 and #84 pinned the validation surface of the
fee-table account (disc wrong 3002, owner wrong 3007, zero
lamports 3012, check order 3012 > 3007 > 3002, key swaps all
3007) and of the GlobalConfig account (disc wrong
InvalidAccountData, owner wrong 3007, zero lamports 3012, check
order 3012 > 3007 > InvalidAccountData, key swaps split by
owner/existence) on this chain. This packet pins the same
surface for the route pools themselves (the 300-byte accounts
at the main, middle, and tail hops): does a wrong
discriminator, a wrong owner, zero lamports, or a swapped
account key gate the trade, deposit, sweep, boost, and set
legs the same way -- and is the gate code the same?

Route: the split x boost x tf chain at TRUE 3 hops (the
`three_amm`-only route 3rd #63/#64 pinned; no g4/g5 hop group is
appended, final output U3). The quote mint carries a 100 bps
transfer-fee config and the split legs route the buyback through
the Token-2022 ATA, as in #64.

## Cases

54 cases, 180 receipts (60 steps x 3 images: original, control
#424, candidate #427), 18 parts of 10 receipts.

- Family A, anchors (4): mhbuy3 / mhsell3 in 10^9, single-leg
  v2 buy2 / sell2 in 10^10, all at bps 100.
- Family D, discriminator (10): main-pool disc zeroed, flipped,
  replaced with the GlobalConfig discriminator, replaced with
  the fee-table discriminator; middle-pool disc zeroed; tail-pool
  disc zeroed; each on buys and, where the hop order matters,
  on sells; plus disc-zero on a single-leg v2 buy.
- Family T, whole-data swaps (3): main-pool data replaced with
  GlobalConfig data, fee-table data, or zeros (length kept at
  300).
- Family O, owner (8): main-pool owner changed to SPL Token,
  Token-2022, System Program, the default pubkey, or the Fees
  program; buy, sell, and single-leg v2 buy/sell with the SPL
  Token owner.
- Family L, lamports (5): 0, 1, and 2,000,000 (below
  rent-exempt for a 300-byte account); buy, sell, and
  single-leg v2 buy at 0.
- Family X, combined faults / check order (5): disc+owner,
  lamports+disc, lamports+owner, all three, disc-flip+owner
  (System) on a sell.
- Family K, instruction account-key swaps (7): the main-pool
  key replaced with the fee-table key, the GlobalConfig key,
  a fresh key with no account, or the user quote account; the
  middle-pool key replaced with the main-pool key; the
  tail-pool key replaced with the middle-pool key; the
  fee-table key on a sell.
- Family P, leg parity (6): disc-zero legacy buy / legacy
  sell, owner-Token legacy buy, disc-zero deposit, disc-zero
  Token-2022 sweep, disc-zero boost (vq patched to 10^9).
- Family W, downstream after a validation failure (4):
  tail-pool failure then main-pool Token-2022 protocol sweep
  + creator sweep + collect; tail-pool failure then boost
  (vq 10^9); tail-pool failure then token claim (seeded UVA,
  claim bps 100); tail-pool failure then cashback claim
  (plain-quote mode, seeded earned 5,475).
- Family S, setters (2): disc-zero and owner-Token
  set_coin_creator on the main pool.

## Result

All 54 cases agree on all three images (0 divergent cases).
Every failure step rolls back every watched account except the
fee payer (fee 5,000).

Anchors (bps 100). mhbuy3 in 10^9: user quote -10^9, tail
output U3 5,262,910,281,902, Token-2022 buyback 4,515,471,
withheld vq1 10,000,000 and buyback 45,611, 3 hop events
(disc 67f4521f2cf57777, len 508 each). mhsell3 in 10^9: user
quote +178,541, withheld user quote 1,804 and buyback 9, 3 hop
events (disc 3e2f370aa503dc2a, len 449 each). buy2 in 10^10:
user base +10^10, user quote -1,866,375, buyback 8,401.
sell2 in 10^10: user quote +1,784,093, buyback 8,401.

Discriminator: every disc fault fails **InvalidAccountData**
(zeroed, flipped, GlobalConfig disc, fee-table disc,
whole-data GlobalConfig/fee-table/zero swaps alike), on every
leg tried (multi-hop buy/sell, single-leg v2 buy, legacy
buy/sell, deposit, Token-2022 sweep, boost, set_coin_creator).
The pool discriminator gate is the same Anchor
deserialization gate as GlobalConfig's -- not the fee-table
account's custom 3002.

Owner: the code depends on the leg. On multi-hop, any owner
other than the pump program fails **6027
AccountTypeNotSupported** (SPL Token, Token-2022, System
Program, default pubkey, Fees program all alike, on buy and
sell): this is the `is_curve_hop` gate in
multi_hop_swap.rs, which requires each hop pool's owner to
be the pump program (AMM hop) or PUMP (curve hop) and
rejects anything else with 6027. On single-leg v2, legacy,
and set legs the same fault fails **3007** (Anchor's owner
check). So the pool owner gate is 6027 on multi-hop but
3007 everywhere else -- unlike #83/#84, where the owner
code was leg-independent.

Lamports: 0 fails **6027 on multi-hop** but **3012 on
single-leg v2**. The multi-hop 6027 is the same owner gate,
not a lamports gate: a 0-lamport account vanishes from the
VM, so the program reads a default account whose owner is
neither the pump program nor PUMP. The v2 3012 is Anchor's
initialized check. 1 lamport and 2,000,000 lamports both
succeed with anchor-identical outputs, so no rent-exempt
minimum is checked -- existence only, exactly as #83/#84
found for the fee-table and GlobalConfig accounts.

Check order: on multi-hop there is no distinguishable
order -- disc+owner, lamports+disc, lamports+owner, and all
three combined all fail **6027**. The 6027 owner/existence
gate fires before any discriminator read, so a combined
fault never reaches the InvalidAccountData that a lone disc
fault reports. This collapses #83's 3012 > 3007 > 3002 and
#84's 3012 > 3007 > InvalidAccountData into a single
6027-first gate on multi-hop.

Key swaps: the fee-table key, the GlobalConfig key, a fresh
key with no account, and the user quote account all fail
**6027** on multi-hop (none is owned by the pump program
or PUMP), on buys and on sells. Swapping in another pool's
key is different: it passes the account gates (owner is the
pump program, discriminator is a pool discriminator) and
fails deeper with **6008 InvalidBaseMint** -- the swapped
pool's stored base/quote mints do not match the hop's route
mints. Middle-pool-as-main fails after 1 ghost event,
tail-pool-as-middle after 2, which also pins the failing
hop by position.

Ghost events pin the failing hop. On buys the hop order is
main, middle, tail: a main-pool failure has 0 ghost events,
a middle-pool failure has 1 (the main hop's event), a
tail-pool failure has 2. On sells the order reverses
(tail, middle, main): a tail-pool failure has 0 ghosts, a
middle-pool failure has 1, a main-pool failure has 2. The
ghost events are the earlier hops' real hop events
(buy disc 67f4521f2cf57777 len 508, sell disc
3e2f370aa503dc2a len 449); the failed hop emits nothing
and the whole transaction still rolls back.

Downstream after a validation failure: legs that read a
different, valid pool keep working at fixture values. After
a tail-pool buy failure, the main-pool Token-2022 protocol
sweep discharges 2,488 (2,463 net, withheld 25), the creator
sweep discharges 123,394 (122,160 net, withheld 1,234),
collect pays 122,160 (120,938 net, withheld 1,222); boost
burns 5,338,379,201,831, equal to the #64 tf100 anchor
because the failed trade left the boost window (vq 10^9 +
accrued buckets) untouched; token claim pays 3,334,551
(3,301,205 net, withheld 33,346); cashback claim pays the
full seeded 5,475. A failed hop therefore leaks nothing
downstream -- unlike #84, where the failed account was
read by the downstream legs themselves, here the downstream
legs read other accounts and are unaffected.

Setters: with disc zeroed, set_coin_creator fails
InvalidAccountData; with the owner set to SPL Token it
fails 3007 -- the same leg codes as the trade legs.

## Limits

- The cashback-claim downstream case uses plain-quote mode:
  as #67 found, a cashback claim on the transfer-fee-override
  quote mint fails with Anchor's ConstraintTokenTokenProgram,
  so the claim family is measured on the plain mint with the
  no-withheld-authority guard.
- Boost is measured here only as a failure leg (disc zeroed)
  and as a downstream leg after a tail-pool failure; boost
  success under a valid config is pinned in #34/#64.
- The 6027 reading (owner gate via `is_curve_hop`) is the
  local source's account-owner branch in multi_hop_swap.rs;
  error sites (source lines) are pinned per image in
  report.json.gz and are never compared across images, since
  the original and rebuilt sources differ in line numbers.
- Fixture values are the #64 chain fixture: pool
  virtual_quote_reserves -125,882, protocol_fees 2,488,
  creator_fees 123,394, lp_supply 4,194,352,106,721.
- No success case for set_coin_creator is included here; the
  set control (silent no-op on an already-set pool) is
  pinned in #70.

Reproduce: `python3 verify.py` from this directory. The
verifier re-checks every receipt signature, every per-image
expected delta / withheld / pool / UVA / GlobalConfig state,
every event, every error code and rollback, GVOL invariance,
and control == candidate on every case.

Made via @slopdotcash
