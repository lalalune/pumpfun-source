# Multi-hop split x boost x tf chain with admin setter legs

## Problem

The split x boost x transfer-fee chain (true 3-hop, `three_amm` only,
final output U3) is now pinned across claim, lifecycle, withdraw-withheld
and coin-creator legs. This packet pins the remaining admin surface on
the same chain: the four admin setters (`update_buyback_config`,
`update_fee_config`, the mode toggles, and `disable`) and how each one
binds to the chain. The question is not whether the setters work in
isolation -- 2nd-run packets #42/#43/#46/#28 already pinned that -- but
whether they move, gate, or leave untouched a live split chain, and
whether the global mode flags and the per-pool mode flags are the same
gate (they are not).

## Route

True 3-hop only. `build_route` calls `three_amm` and nothing else; the
P4/P5 fixture pools exist for snapshots but are outside the route, and
the final output is U3. No g4/g5 hop group is appended (contrast 3rd #61,
whose name said 3-hop but whose route appended g4 and was really 4 hops).

All cases run under tf100 (quote mint transfer fee 100 bps) unless noted.
Program images: original (`6a7ad345...`), control (`7a300434...`),
candidate (`d17a657b...`); every case is reproduced on all three.

## Cases

31 cases, 219 receipts (73 steps x 3 images), 22 parts (21 x 10 + 9).

### Family A -- update_buyback_config (bps 5000 baseline)

- `a-anchor-mhbuy-swc-col`: anchor mhbuy3 -> sweep -> collect.
- `a-bb7500-mhbuy-swc-col`: bps 5000 -> 7500, then the anchor chain.
- `a-bb10000-mhbuy`: bps -> 10000, then mhbuy3.
- `a-bb0-mhbuy`: bps -> 0, then mhbuy3.
- `a-bb10001-fail-mhbuy`: bps 10001 rejected, then mhbuy3 (anchor-identical).
- `a-bb-recip-excl-mhbuy`: bps unchanged, recipients replaced with 8 keys
  that exclude the fixture buyback owner, then mhbuy3.
- `a-bb-outsider`: setter signed by a non-admin.
- `a-bb-unsigned`: setter with the admin account not signing.
- `a-bb-none-noop-mhbuy`: bps None + no recipients (silent no-op), then mhbuy3.

### Family B -- update_fee_config

- `b-ufc-base-mhbuy-swc-col`: lp 20 -> 30, proto 5 -> 40, creator 5 -> 100,
  new sorted recipients, new fee authority, then the anchor chain.
- `b-ufc-unsorted-fail-mhbuy`: descending recipients rejected, then mhbuy3.
- `b-ufc-lp1001-fail`: lp 1001 with descending recipients (bps checked first).
- `b-ufc-outsider`: setter signed by a non-admin.
- `b-ufc-tiercap` / `b-tiercap-anchor`: fee tiers patched in place
  (tier 100 -> (10, 111, 333), tier 185,000,000,000 -> (20, 222, 444)),
  mhbuy3 twice, with and without the preceding fee-config update.

### Family C -- mode toggles

- `c-tog-mayhem-off`: mayhem True -> False, then False again (same-state).
- `c-tog-cashback-off`: cashback True -> False, then False again.
- `c-tog-boost-samestate`: boost True -> True (already enabled).
- `c-tog-outsider`: mayhem toggle signed by a non-admin.
- `c-tog-cb-off-cbflag-mhbuy`: global cashback off, then a buy on a
  cashback-flagged non-terminal pool.
- `c-cbflag-mhbuy-anchor`: same buy with the global flag still on.
- `c-tog-mayhem-off-mayhemflag-mhbuy`: global mayhem off, then a buy on
  a mayhem-flagged non-terminal pool.

### Family D -- disable setter

- `d-dis-buy-mhbuy-fail`: buy bit set, mhbuy3, bit cleared, mhbuy3.
- `d-dis-sell-mhsell-fail`: sell bit set, mhsell3, bit cleared, mhsell3.
- `d-dis-dep-fail`: deposit bit set, deposit, bit cleared, deposit.
- `d-dis-wd-fail`: withdraw bit set, withdraw, bit cleared, withdraw.
- `d-dis-buy-boost`: buy bit set, boost, bit cleared, mhbuy3.

### Family E -- setter neutrality

- `e-neutral-setters-mhbuy-boost`: buyback None + boost same-state True +
  disable all false, then mhbuy3 + boost (vs the mhbuy3 + boost anchor).

## Result

### Buyback bps moves the chain linearly, tail output untouched

Baseline (bps 5000) mhbuy3: buyback leg 4,515,471, tail output U3
5,262,910,281,902, vq1 credit 985,438,918. After the setter:

| bps | buyback leg | withheld bb22 | vq1 credit | U3 |
|-----|-------------|---------------|------------|----|
| 5000 | 4,515,471 | 45,611 | 985,438,918 | 5,262,910,281,902 |
| 7500 | 6,773,206 | 68,417 | 983,158,377 | 5,262,910,281,902 |
| 10000 | 9,030,942 | 91,222 | 980,877,836 | 5,262,910,281,902 |
| 0 | (no leg) | 0 | 990,000,000 | 5,262,910,281,902 |

The buyback leg scales exactly with bps (7500 = 1.5x, 10000 = 2x of
baseline) and is taken out of the vq1 credit; the tail output never
moves. The setter itself emits no event and only rewrites GlobalConfig
bytes 899..907 (bps) or 643..899 (recipients).

### Buyback setter gates, all reproduced on the chain

- bps 10001 -> Custom 6056, full rollback, following mhbuy3
  anchor-identical.
- Recipients excluding the fixture buyback owner -> the following
  mhbuy3 fails Custom 6053 (the multi-hop buy checks buyback-owner
  authorization the same way a single-pool buy does).
- Non-admin signer -> 6005; unsigned admin account -> 3010; both with
  no config change.
- bps None + no recipients -> silent success, no config change, chain
  anchor-identical.

### update_fee_config rewrites config but leaves the chain byte-identical

The setter (lp 30, proto 40, creator 100, sorted new recipients, new
authority `6363...63`) succeeds and emits a 360-byte event
(disc `5a1741233ef4bcd0`: admin, lp 30, proto 40, 8 recipients,
creator 100, authority), and GlobalConfig shows lp 20 -> 30,
proto 5 -> 40, creator 5 -> 100, fee authority rewritten. The following
mhbuy3 + sweep + collect chain is nevertheless byte-identical to the
anchor: the split chain prices off feeconfig tiers, not the global
lp/proto/creator bps. The tier-cap crossing case is likewise unmoved
by a preceding fee-config update (both mhbuy3 legs identical to the
no-update anchor: first leg U3 5,212,091,891,000, second leg
4,972,170,179,853).

### Fee-config gates: order and atomicity

- Descending recipients -> 6012, no config change, following mhbuy3
  anchor-identical (no partial application).
- lp 1001 with descending recipients -> 6000, not 6012: the bps bound
  is checked before the recipient ordering.
- Non-admin signer -> 6005, no config change.

### Mode toggles: global flags are separate from pool flags

- mayhem True -> False rewrites GlobalConfig byte 417 (1 -> 0); a
  second False -> 6043 (same-state).
- cashback True -> False rewrites byte 642 (1 -> 0); a second False ->
  6051 (same-state).
- boost True -> True succeeds silently with no config change: unlike
  mayhem/cashback, `toggle_boost` has no same-state check.
- Non-admin toggle -> 6005. Toggles emit no event.
- The cashback divergence survives the global toggle: a buy on a
  cashback-flagged non-terminal pool succeeds on the original and
  fails 6079 on the rebuild, whether the global cashback flag is on
  (`c-cbflag-mhbuy-anchor`) or off (`c-tog-cb-off-cbflag-mhbuy`).
  The global flag and the pool flag are separate gates, and the
  rebuild's per-hop gate does not consult the global flag either.
- A buy on a mayhem-flagged non-terminal pool fails 6080 on all three
  images even with the global mayhem flag off: the mayhem gate is
  per-hop on every image and does not consult the global flag.

### Disable setter: all four gates bind, boost is buy-gated, recovery is exact

- Buy bit (disable byte 0 -> 8) -> mhbuy3 fails 6020; clearing the bit
  restores the anchor chain byte-identically. Disable emits a 53-byte
  event (disc `6bfdc14ce4ca1b68`: timestamp, admin, 5 bools).
- Sell bit (0 -> 16) -> mhsell3 fails 6021; recovery anchor-identical.
- Deposit bit (0 -> 2) -> deposit fails 6018; recovery deposit succeeds
  (user LP +1,000,000,000, quote -29,608,495).
- Withdraw bit (0 -> 4) -> withdraw fails 6019; recovery withdraw
  succeeds (user LP -1,000,000,000, quote +29,019,284).
- Boost under buy-disabled fails 6020: boost routes through an internal
  buy, so the buy gate applies to it too. Clearing the bit restores
  the anchor mhbuy3.

### Setter neutrality

The no-op setter trio (buyback None, boost same-state True, disable all
false) leaves mhbuy3 + boost byte-identical to the anchor: mhbuy3 U3
5,221,217,806,636, boost burn 5,255,205,915,165. Setters themselves do
not move prices.

### Divergence

2 divergent cases, both the cashback-flagged non-terminal hop pattern
already seen in 3rd #25/#43/#67: original succeeds, rebuild fails 6079.
Control and candidate agree everywhere else. This is a rebuild
difference in gate placement (terminal-only vs every hop), not a
difference in setter behaviour: the setters themselves behave
identically on all three images in every case.

## Limits

- All measurements are LiteSVM reproductions against the fixture
  pools and the three program images; no mainnet state is involved.
- The buyback bps ladder is measured at 0 / 5000 / 7500 / 10000 only;
  intermediate bps values were not swept.
- The fee-config update uses one recipient set and one authority; the
  "chain unmoved" result is for the split chain's tier pricing, not a
  claim that global bps never affect any path (single-pool v2 trades
  price off them).
- The disable recovery cases re-enable with a single all-false call;
  per-bit selective re-enabling was not separately measured.

Made via @slopdotcash
