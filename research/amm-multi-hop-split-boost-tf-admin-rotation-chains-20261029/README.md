# research: split-chain trades ignore admin rotation — setter handover, admin-agnostic sweep/collect, boost follows boost authority, fee-authority separation

## Problem

The brief for this packet was to compose the 2nd-run #27 admin
authority rotation bridge onto the split×boost×tf chain (true 3 hops,
`three_amm` only, final output U3): after the GlobalConfig admin is
replaced, which split-chain legs still answer to the old admin, which
answer to the new one, and does the chain itself notice the rotation?
Measurement first established the rotation primitive, then ran every
leg of the chain through it. The answer splits four ways. Trades do
not notice at all: split buy/sell tail output and buyback legs are
byte-identical before and after rotation. Setters hand over
completely: the old admin's disable, buyback-config, fee-config, and
mode-toggle calls all fail 6005 after rotation, the new admin's all
succeed, and the rotation round-trips. Sweep and collect are
admin-agnostic in the other direction: both the old and the new
admin sweep and collect successfully for the same amounts — the
sweep/collect handlers never check the admin field. Boost follows
neither the old nor the new admin: it follows the boost authority,
a separate GlobalConfig field (907..939) that rotation leaves
untouched, so a rotated admin's boost still succeeds and only a
boost-authority rotation blocks it (6005).

Route confirmation (from the builder itself): the fixture route calls
`three_amm` only and appends no g4/g5 hop group — 3 hop groups, final
output U3. This packet does not repeat 3rd #61's naming error (a "3-hop"
packet whose builder actually appended a P4 group).

One scope note, measured first: the rotation instruction takes the
new admin as an account and validates nothing about it — self,
unfunded, and even the program id itself all succeed as the new
admin, and a zero-pubkey rotation bricks the config (afterwards
neither the old nor the new admin can act, since nobody can sign
for the zero key). The fee authority (321..353) is a third, separate
field: rotating the admin leaves it alone, and rotating back after a
fee-authority change keeps the changed fee authority. All rotation
steps in this packet use the fixture payer as the starting admin and
the outsider key `5jotNjSnm9ZJRefVfqHato9FC4d9t6CHb2xS1726MTyY` as the
new admin, unless noted.

## Cases

25 cases, 66 steps, 198 receipts (66 steps × 3 images), 20 parts
(19×10 + 8). All cases run the same steps on the original, control
(#424) and candidate (#427) images. All cases run under tf100 on the
quote mint unless noted. Rotation cases use the outsider key above
as the new admin; the program id and the zero pubkey appear as new
admins where noted.

Family R — rotation storage alone (7 cases):

- `r-rot-outsider`: rotate admin payer → outsider. Succeeds; only
  GlobalConfig bytes 8..40 change; 80-byte UpdateAdminEvent
  (disc `e198ab57f63f42ea`, ts 1234567890, old admin → new admin).
  Fee authority (321..353) and boost authority (907..939) unchanged.
- `r-rot-self`: rotate admin payer → payer. Succeeds (no-op write).
- `r-rot-unfunded`: rotate admin payer → unfunded key. Succeeds.
- `r-rot-program`: rotate admin payer → the program id. Succeeds
  (no validation of the new admin).
- `r-rot-outsider-signer`: rotation signed by the outsider while the
  admin is still the payer. Fails 6005, full rollback.
- `r-rot-unsigned`: rotation with the admin account not signing.
  Fails 3010, full rollback.
- `r-rot-default-brick`: rotate admin payer → zero pubkey, then
  disable-buy signed by the payer and by the outsider. Rotation
  succeeds; both disable calls fail 6005 — the config is bricked.

Family C — chain after rotation (4 cases):

- `c-anchor`: mhbuy3 of 10^9, no rotation. Tail output U3
  +5,262,910,281,902; buyback leg +4,515,471; withheld vq1
  10,000,000 and buyback 45,611.
- `c-rot-buy`: rotation, then mhbuy3. Tail output, buyback leg,
  and withheld figures byte-identical to the anchor.
- `c-rot-sell`: rotation, then mhsell3 of 10^9. Quote out
  +178,541; buyback leg +837; withheld userquote 1,804 and
  buyback 9 — identical to a pre-rotation sell.
- `c-rot-buy-buy`: rotation, then two mhbuy3 legs. Second leg
  matches a second pre-rotation leg exactly.

Family S — setters after rotation (5 cases):

- `s-dis-bind`: rotation, then disable-buy signed by the old admin
  (6005, rollback), disable-buy signed by the new admin (succeeds,
  53-byte DisableEvent disc `6bfdc14ce4ca1b68`, bools
  [0,0,0,1,0]), mhbuy3 (6020 — buy disabled), disable-clear signed
  by the new admin (succeeds), mhbuy3 (anchor again).
- `s-bbcfg`: rotation, then buyback-config 7500 signed by the old
  admin (6005), signed by the new admin (succeeds), then mhbuy3:
  buyback leg 6,773,206 — exactly 1.5× the 5000-bps anchor leg.
- `s-ufc`: rotation, then fee-config (lp 30, protocol 40, creator
  100, sorted recipients, authority 0x63×32) signed by the old admin
  (6005), signed by the new admin (succeeds, 360-byte event disc
  `5a1741233ef4bcd0`), then mhbuy3 (anchor byte-identical —
  fee-config changes do not move the chain).
- `s-tog`: rotation, then mayhem-toggle-off signed by the old admin
  (6005), signed by the new admin (succeeds), signed by the new
  admin again (6043 — already off).
- `s-roundtrip`: rotation payer → outsider, rotation back
  outsider → payer (signed by the outsider as current admin),
  disable-buy signed by the payer. Succeeds — the handover is
  reversible.

Family W — sweep/collect after rotation (4 cases):

- `w-swp-old`: rotation, mhbuy3, protocol sweep signed by the old
  admin. Succeeds: 4,563,570 out of the pool, proto22 net
  +4,517,934, withheld 45,636.
- `w-swp-new`: rotation, mhbuy3, protocol sweep signed by the new
  admin. Succeeds with identical amounts.
- `w-col-old`: rotation, mhbuy3, creator sweep and collect signed
  by the old admin. Succeeds: creator sweep 123,394 out,
  creat22 +122,160; collect fee 122,160, dest22 +120,938,
  withheld 1,222.
- `w-col-new`: same legs signed by the new admin. Identical
  amounts. Sweep/collect never consult the admin field.

Family B — boost vs admin and boost authority (4 cases):

- `b-rot-boost`: vq patched to 10^9, rotation, then boost of 10^9
  signed by the old admin. Succeeds: burn 5,338,379,201,831,
  vq 1,000,000,000, quote_after 123,936,690,720, base_after
  668,358,016,710,914, remaining 999,000,000,000. Rotation does
  not touch boost.
- `b-boostauth`: vq patched to 10^9, boost authority rotated to the
  outsider (112-byte SetBoostAuthorityEvent disc
  `5980f08d5bca4769`, only bytes 907..939 change), boost signed
  by the old authority (6005), boost signed by the new authority
  (succeeds, same burn 5,338,379,201,831).
- `b-rot-boostauth`: vq patched to 10^9, admin rotation, then
  boost-authority rotation signed by the old admin (6005 —
  boost-authority rotation checks the admin), signed by the new
  admin (succeeds), boost signed by the new authority (succeeds,
  same burn).
- `b-rot-boost-window0`: rotation, then boost with no vq patch
  (window 0). Fails 6065 — the zero-window gate is unchanged by
  rotation.

Family E — fee-authority separation (1 case):

- `e-feeauth`: rotation payer → outsider, fee-config change by the
  new admin moving the fee authority to 0x63×32, rotation back
  outsider → payer. Final config: admin = payer, fee authority =
  0x63×32. The fee authority survives an admin round-trip, and the
  admin rotation never moved it.

## Result

0 divergent cases across the original, control (#424), and candidate
(#427) images: every case's observed surface (balances, pool states,
config fields, events, error codes, rollback) is identical on all
three images. The split chain is admin-blind (trades byte-identical
across rotation), setters hand over atomically (old admin 6005, new
admin success, round-trip works), sweep/collect are admin-agnostic
(both admins succeed for identical amounts), boost answers only to
the boost authority (rotation-neutral; boost-authority rotation
gates at 6005), and the fee authority is a third independent field
that survives admin rotation in both directions. The unvalidated
new-admin acceptance (including the program id) and the
zero-admin brick are pinned as measured, not as claimed defects:
rotation writes exactly bytes 8..40 and nothing else.

## Limits

- All measurements are LiteSVM receipts against the three program
  images (original, control #424, candidate #427); no mainnet or
  devnet execution was performed.
- The fixture uses one pool set, one clock (ts 1234567890), and one
  outsider key; other admin keys were not exercised beyond the
  unfunded/program/zero cases above.
- Rotation cases do not cover the remaining admin setters
  (update_token_incentives, update_buyback_config beyond the bps
  leg used here) — those setters' handover follows the same admin
  check but was not separately receipted in this packet.
- No source change is proposed: this packet is a measurement record
  of the admin/fee-authority/boost-authority field separation and
  the split chain's indifference to rotation.

Made via @slopdotcash
