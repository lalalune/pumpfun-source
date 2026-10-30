# research: split-chain trades never feed current_sol_volume — sync reset gate, claim conversion, and chain neutrality

## Problem

The brief for this packet was to compose the 2nd-run #48 track_volume +
current_sol_volume bridge onto the split×boost×tf chain (true 3 hops,
`three_amm` only, final output U3): do split trades feed the user volume
accumulator (UVA), does `sync_user_volume_accumulator` ever change
anything, how does accumulated volume convert into a token-claim payout,
and do volume steps move the chain back? Measurement shows the volume
pipeline has no producer on the split chain at all, sync is a narrow
reset gate, and claim conversion is a fixed previous-day ratio — all
pinned below with fresh numbers, not copied from 2nd #48.

Route confirmation (from the builder itself): the fixture route calls
`three_amm` only and appends no g4/g5 hop group — 3 hop groups, final
output U3. This packet does not repeat 3rd #61's naming error (a "3-hop"
packet whose builder actually appended a P4 group).

One scope note, measured first: the multi-hop route has no track
argument at all — its hop events only echo the UVA's stored
`current_sol_volume` (`multi_hop_swap.rs:822`, same echo in
`buy.rs:375`, `trade_v2.rs:291/323`, `trade.rs:206`). The only track
input in the program is legacy buy's trailing OptionBool byte. So
family D tests track 0 vs 1 on legacy buy adjacent to the split chain,
and families A–C test the split route itself. There is no pool-level
track flag to toggle on the multi-hop route.

The no-fee baseline here is bps 0 *with* the transfer-fee override
(tf0), not plain-quote mode: in this builder's setup the plain route
(SPL buyback) fails `InvalidAccountData` on the first hop (probed, not
debugged further), while tf0 trades cleanly and reproduces the plain
tail exactly (buy 10^9 tail 5,315,084,721,958, identical to 3rd #67's
plain-quote tail).

## Cases

32 cases, 50 steps, 150 receipts (50 steps × 3 images), 15 parts of 10
receipts. All cases run the same steps on the original, control (#424)
and candidate (#427) images. Seeded UVA fixture, unless noted:
needs_claim 1, total_unclaimed 111, total_claimed 222,
current_sol_volume 333444, last_update_timestamp 20,
has_total_claimed_tokens 1, cashback_earned 555, total_cashback_claimed
666. Global volume accumulator fixture: start_time 20, end_time 49,
seconds_in_a_day 1, total_token_supply 1000 per day, sol_volumes 100
per day. Sync steps run at clock timestamp 10, claim steps at 21.

Family A — split trades never move a seeded UVA, tf100 (6 cases):

- `a-buy1e9`: split buy 10^9 quote in.
- `a-sell1e9`: split sell 10^9 base in.
- `a-buy1e6`: split buy 10^6 quote in.
- `a-sell1e6`: split sell 10^6 base in.
- `a-buy-sell`: buy 10^9 then sell 10^9.
- `a-sell-buy`: sell 10^9 then buy 10^9.

Family B — same invariance, tf0 baseline (3 cases):

- `b-buy1e9`, `b-sell1e9`, `b-buy-sell` (same sizes as family A).

Family C — fresh UVA auto-creation (3 cases, no seed):

- `c-buy`: first split buy on an absent UVA.
- `c-buy-buy-sell`: buy 10^9, buy 10^6, sell 10^9 on a fresh UVA.
- `c-sell`: first split sell on an absent UVA.

Family D — legacy buy track byte adjacent to the split chain, tf100 (4 cases):

- `d-leg0-buy`: legacy buy (track 0) then split buy 10^9.
- `d-leg1-buy`: legacy buy (track 1) then split buy 10^9.
- `d-leg1`: legacy buy (track 1) alone.
- `d-leg1-fresh`: legacy buy (track 1) on a fresh UVA.

Family E — sync reset gate, tf100 (7 cases):

- `e-sync-last10`: sync, seeded last_update 10.
- `e-sync-last19`: sync, seeded last_update 19.
- `e-sync-last20`: sync, seeded last_update 20.
- `e-sync-last21`: sync, seeded last_update 21.
- `e-sync-claimed0`: sync, claimed already 0, last_update 10, has flag 1.
- `e-sync-gva-absent`: sync with the global accumulator account absent.
- `e-trade-sync-last10`: split buy 10^9, then sync, last_update 10.

Family F — claim conversion of seeded volume, tf100 (5 cases):

- `f-claim`: token claim alone.
- `f-trade-claim`: split buy 10^9, split sell 10^9, then claim.
- `f-claim-last10`: claim with last_update 10 (before incentive start).
- `f-sync-claim`: sync (last_update 10), then claim.
- `f-claim-twice`: claim, then claim again.

Family G — volume steps never move the chain, tf100, main-pool
virtual_quote_reserves patched to 10^9 (4 cases):

- `g-buy-boost`: split buy 10^9, then boost 10^9.
- `g-buy-sync-boost`: split buy 10^9, sync, then boost 10^9.
- `g-buy-claim-boost`: split buy 10^9, claim, then boost 10^9.
- `g-claim-buy`: claim, then split buy 10^9.

## Result

(a) Split trades never move the UVA. On the seeded fixture the UVA is
byte-identical after every split step in families A and B: needs 1,
unclaimed 111, claimed 222, volume 333444, last 20, has 1, earned 555,
cb_claimed 666 — buy and sell, 10^6 and 10^9, tf100 and tf0, single
steps and buy↔sell pairs. The chain itself still moves normally:
tf100 buy 10^9 spends the full 10^9 quote, tail output U3
5,262,910,281,902, TOKEN22 buyback +4,515,471, withheld vq1
10,000,000 / buyback 45,611; tf100 sell 10^9 returns 178,541 quote,
buyback +837, withheld userquote 1,804 / buyback 9; tf0 buy 10^9 tail
5,315,084,721,958, buyback +4,607,153, no withholding; tf0 sell 10^9
returns 180,345 quote. So the tf100 sell costs 1,804 quote against
tf0 (180,345 − 178,541), and none of it lands in the UVA.

(b) Track on/off changes nothing either. Legacy buy emits a 497-byte
event whose byte 360 is the track byte (0 for `d-leg0-buy`, 1 for
`d-leg1-buy` / `d-leg1`), but the UVA is byte-identical after both,
and the following split buy also leaves it identical. The multi-hop
route takes no track input, so there is no track-on split-chain
variant to compare against — the track dimension exists only on
legacy buy, and it is volume-neutral there too (consistent with
2nd #48's legacy finding, now re-measured adjacent to the split
chain).

(c) Sync is a narrow reset gate, and its no-op now has a cause. Source:
`programs/pump-amm/src/incentives.rs:15-20` (`reset` zeroes
total_claimed_tokens only when `now < g.start_time` AND
`last_update_timestamp < g.start_time`) and `:22-34` (`sync` calls
only `reset`, then emits an event only if total_claimed_tokens
changed, else logs "No changes in accumulator"). Measured against
the fixture (start_time 20, sync clock 10): last_update 10 and 19
both fire — claimed 222 → 0, has flag 1 → 0, one 64-byte event
(disc `c57aa77c74515bff`, before 222, after 0, ts 10), all other
fields untouched (volume stays 333444, unclaimed stays 111);
last_update 20 and 21 are no-ops — 0 events, "No changes in
accumulator" in the log, UVA byte-identical. The claimed-already-0
case (last_update 10, has 1) is the instructive middle: `reset`
fires and flips has 1 → 0, but before == after == 0, so no event
is emitted and the log still says "No changes" — the message
reports the claimed-tokens comparison, not whether `reset` ran.
Sync after a split trade (`e-trade-sync-last10`) fires identically
to sync alone, because the trade never touched the gate inputs.
Sync with the global accumulator absent fails 3012 with full
rollback (fee −5,000 only).

(d) Claim converts seeded volume at a fixed previous-day ratio, and
only when the reward branch can fire. Source:
`incentives.rs:96-101` (reward = current_sol_volume ×
total_token_supply[previous_day] / sol_volumes[previous_day],
then volume → 0) and `:124-125` (claim zeroes unclaimed, adds to
claimed, reports volume in the event). Measured: seeded claim pays
3,334,551 = 111 unclaimed + 333,444 × 1000 / 100 reward; event
(disc `4facf631cd5bcee8`, len 104) reports amount 3,334,551,
total_claimed 3,334,773, current_sol_volume 0; UVA after: needs 0,
unclaimed 0, claimed 3,334,773, volume 0, last 21, has 1.
Trade-then-claim pays exactly the same 3,334,551 — the two split
trades added nothing to convert. But with last_update 10 (before
start_time 20), the reward branch is skipped (claim requires
last_update ≥ start_time): claim pays only the 111 unclaimed,
volume stays 333444, claimed 222 → 333, last → 21, needs stays 1
(because volume > 0). Sync-then-claim composes exactly: sync
zeroes claimed 222 → 0, then claim pays the same 111, claimed
ends at 111, volume still 333444. Claim-twice: the second claim
emits 0 events and logs "No tokens to claim", UVA unchanged.

(e) Volume steps never move the chain. In family G the boost event
is byte-identical across buy-only, buy+sync, and buy+claim:
requested 1,000,000,000, used 1,000,000,000, burned
5,255,205,915,165, vq 995,438,918, quote_after 124,922,129,638,
base_after 663,151,614,046,382, remaining 999,000,000,000. And
claim-then-buy deltas equal buy-alone deltas exactly
(`g-claim-buy` buy step == `a-buy1e9`). Sync, claim, and track
steps touch no pool, vault, or buyback account.

Divergence: 0 cases. Original, control, and candidate agree on all
32 cases; control and candidate surfaces are identical everywhere.

## Limits

- Plain-quote (SPL buyback) mode is not covered: in this builder's
  setup the plain multi-hop route fails `InvalidAccountData` on the
  first hop (probed; the failure was not debugged further, and no
  plain-mode case is claimed). The no-fee baseline is tf0 with the
  transfer-fee override.
- The global accumulator fixture is fixed (start 20, end 49, one
  second per day, supply 1000 / sol_volumes 100 per day); the sync
  clock is fixed at 10 and the claim clock at 21 by the harness
  steps. The reset gate is therefore pinned at the last_update 19 /
  20 boundary, not across arbitrary start times.
- Only the true 3-hop split route is covered; 4- and 5-hop routes
  were not re-measured here, and mayhem-mode pools are not covered
  (mayhem source is absent from the sparse checkout).
- The "No changes in accumulator" log line is not by itself proof
  that `reset` did not run: the claimed-0 case shows `reset` flipping
  the has flag with no event and the same log line.

Made via @slopdotcash
