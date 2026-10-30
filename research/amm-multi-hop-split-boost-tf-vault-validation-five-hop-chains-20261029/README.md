# Vault and token-account validation on the split x boost x tf chain at TRUE 5 hops

Packet #142 of the pumpfun-source 3rd run. Extends packet #88's
vault/token-account validation findings from a 3-hop chain to a TRUE
5-hop split x boost x tf chain: `three_amm` + g4 + g5, final output
U5. The route is verified in code (build_route calls three_amm, then
appends g4 and g5, tail re-pointed to U5) and by event counts: the
successful 5-hop buy and the successful 5-hop sell each emit 5 hop
events.

## Problem

On a multi-hop swap, each hop's vaults pass through several gates
before the hop's transfers run: Anchor initialization, the Anchor
TokenAccount owning-program gate, the token program's mint check,
the ATA-owner check, lamport/amount/state checks, and the per-hop
pool-binding check (instruction account keys vs the pool's stored
vault keys). #88 pinned those gates at 3 hops. This packet asks
whether the same gates, the same check order, and the same ghost
counts hold at depth 5 -- and whether any vault field that was
checked at 3 hops stops being checked when the vault sits four
hops deep.

## Cases

123 cases, 411 receipts (137 steps x 3 images: original, control,
candidate), 42 parts of 10 receipts each. Families:

- Anchors: 5-hop buy/sell (bps-100 transfer fee), v2 buy/sell,
  legacy buy/sell, deposit, withdraw, sweep, collect, boost,
  token claim, cashback claim.
- Owning program: Token-2022 vault owned by SPL Token, SPL vault
  owned by Token-2022, vault owned by the System Program or by
  the default pubkey -- on main, hop, and tail vaults, both
  directions, and on v2/legacy/deposit/withdraw/sweep/boost legs.
- Mint mismatches: wrong mint on vb1..vb5 and vq1..vq5, on legs,
  and at tf 5000 / tf 0.
- ATA owner: outsider owner on vb1..vb5, vq1..vq5, userquote, U5,
  buyback ATA, user LP.
- Lamports: 0, 1, and 1,000,000 lamports on vaults; rent-only
  native user account; native user account with a zeroed data
  amount field.
- Amount/state: zero-amount quote/base vaults; state byte 0
  (uninitialized) and 2 (frozen).
- Instruction account-key swaps: vault slots holding another
  vault, a fresh key, or a user account key; userquote slot and
  U5 slot swaps.
- Combined faults: lamports-0 + mint, mint + owning program,
  owning program + ATA owner, mint + Token-2022 owner on vq5.
- Downstream after failure: sweep/collect/boost/claim legs run
  after a vq3, vb3, vq5, vb5, or sell-side vault failure.
- Validation-order probes at depth 5 and tf variants (5000, 0).

Retired vs #88: the U3 cases are gone -- U3 is not in the 5-hop
route, so mutating it measures nothing. Every U3 family has a U5
equivalent. The hop-owner map below is the new depth-5 result.

## Result

All 123 cases agree on all three images (0 divergent cases).
Failure steps roll back every watched account except the fee
payer (fee 5,000).

Anchors (bps-100 tf, 5 hop events each direction). Buy: userquote
-1,000,000,000; vb1 -5,332,264,170,203, vq1 +985,438,918; vb2
-5,303,981,938,022, vq2 +5,332,264,170,203; vb3 -5,275,998,139,846,
vq3 +5,303,981,938,022; vb4 -5,248,308,076,854, vq4
+5,275,998,139,846; vb5 -5,207,955,235,891, vq5 +5,248,308,076,854;
u5 +5,207,955,235,891; buyback leg +4,515,471. Pools after: main
[vq -4,686,964, protocol 4,563,570, creator 123,394, lp_supply
4,194,352,106,721]; pool2, p3, p4 all [-125,882, 2,488, 123,394,
same supply]; p5 [-2,617,735,896, 2,488, 2,617,733,408, same
supply]. Sell: userquote +178,541, buyback leg +837, 5 events.

Owning program (Anchor TokenAccount gate accepts either token
program): Token-2022 vault owned by SPL Token ->
IncorrectProgramId (vq1 main, 0 buy ghosts, 4 sell ghosts; also on
buy2, dep, swp22, sell2, legbuy, boost, wd legs). SPL vault owned
by Token-2022 -> ExternalAccountDataModified (vb1 1 buy ghost;
vq2 1; vq3 2; vq4 3; vq5 4 buy ghosts; sell side P5 1, P4 2, P3 3,
P2 4, main 4 ghosts). System-program or default-pubkey owner ->
3007 AccountOwnedByWrongProgram (vq1, vb1, vq2, vq3, vq5, vb5;
vb3-owner sys on sell fails 3007 with 2 ghosts, then the cashback
claim still succeeds).

Mint mismatches -> token-program custom 3 (MintMismatch): vq1 (0
buy ghosts), vb1 (1), vq2 (1), vb3 (3), vq4 (3), vb5 (4), vq5 (4);
also on buy2 and legsell legs; tf 5000 / tf 0 variants identical.
User input/output accounts are validated by route continuity
instead: userquote mint wrong -> 6084
MultiHopDiscontinuousPath (0 ghosts, multi_hop_swap.rs:251); u5
mint wrong -> 6084 (0 ghosts, multi_hop_swap.rs:300).

ATA owner map at depth 5 (the new pin): main quote vault outsider
-> custom 4 (OwnerMismatch), 0 buy ghosts. Base vaults outsider ->
custom 4 at every hop: vb1 1, vb2 2, vb3 3, vb4 4, vb5 4 buy
ghosts. Hop quote-vault ATA owners are NOT checked: vq2, vq3,
vq4, vq5 outsider-owner cases all succeed anchor-identically
(deltas and pools exactly equal to a-buy5; the receipts'
before-snapshots genuinely carry the outsider owner at bytes
32:64). Likewise tail output u5 outsider-owner succeeds
anchor-identically. So the checked set is vq1 + all base vaults;
the unchecked set is hop quote vaults vq2..vq5 + tail output U5.
Mint IS checked on every vault including the hop quote vaults, so
the gap is owner-only. Buyback ATA outsider-owner -> 6053
BuybackFeeRecipientNotAuthorized. User LP outsider-owner on
deposit -> Anchor 2015 ConstraintTokenOwner.

Lamports: 0-lamport vault/user account vanishes from the VM ->
3012 AccountNotInitialized (vq1 0, vb1 0, vq3 2, vq5 4, vb5 4 buy
ghosts; userquote lam0 -> 3012). 1 lamport and 1,000,000 lamports
succeed anchor-identically (no rent-exempt check). Rent-only
native user account (lamports equal to rent-exempt minimum, zero
spendable) -> Token-2022 custom 14 on the buy input transfer.
Native user account with data amount field zeroed (lamports
untouched) -> token custom 1: the transfer reads the data amount
field, not the lamports-derived balance.

Amount/state: zero-amount quote vault -> 6023 Overflow;
zero-amount base vault -> 6025 DivisionByZero (vq5/vb5 both 4 buy
ghosts; vq1/vb1 0 ghosts). State byte 0 (uninitialized) ->
UninitializedAccount; state byte 2 (frozen) -> token custom 17
(vq5 state0/state2 both 4 ghosts).

Instruction account-key swaps (validated per hop against the
pool's stored vault keys): base-vault slot holding another
account -> 6014 InvalidPoolBaseTokenAccount; quote-vault slot
holding another account -> 6015 InvalidPoolQuoteTokenAccount
(both reported against the pool account). Fresh (nonexistent)
key in a vault slot -> 3012 first (initialization check
precedes pool-binding check): vq1 fresh 0 ghosts, vq5 fresh 4
ghosts. userquote slot holding userbase key -> 6084;
u5 slot holding userquote key -> 6084 (0 ghosts).

Check order on a vault is existence > owning program > content:
vq1 lam0 + mint -> 3012; vq1 mint + owner_prog token ->
IncorrectProgramId (0 ghosts); vq1 owner_prog token + owner_acct
outsider -> IncorrectProgramId. vq5 mint base5 + owner_prog
token22 -> custom 3 with 4 ghosts (mint gate fires; the combined
fault does not reach the program gate).

Ghost-count pattern (buy direction, quote-vault faults): ghosts =
hops executed before the failing hop (main 0, P2 1, P3 2, P4 3,
P5 4). Buy direction, base-vault faults: ghosts = quote-fault
ghosts + 1 (the failing hop's own event), except terminal P5
capped at 4 (vb1 1, vb2 2, vb3 3, vb4 4, vb5 4). Sell direction,
quote-vault faults: P5 1, P4 2, P3 3, P2 4, main 4 (the failing
intermediate hop's own SellEvent is included; the terminal main
hop's is not). Mechanism (consistent with #88): events sit
between the in-transfer and the out-transfer for non-terminal
hops, and after the out-transfer for the terminal hop.

Downstream after a vault failure (no leak into main-pool legs):
vq3 mint failure, then swp22/swc22/col22 all succeed; then
patched-window boost succeeds (2 events); then token claim
succeeds (1 event). vb3 owner-sys sell failure (3007, 2 ghosts),
then cashback claim succeeds. vq5 mint failure, then
swp22/swc22/col22 succeed; then patched-window boost succeeds;
then token claim succeeds; sell-side vq5 mint failure (custom 3,
1 ghost), then swp22 succeeds. vb5 owner-sys sell failure (3007,
0 ghosts), then cashback claim succeeds.

Leg parity: the same vault fault fails identically on multi-hop
buy/sell, v2 buy/sell, legacy buy/sell, deposit/withdraw, sweep,
and boost legs. Validation is tf-neutral: vq1 prog-token at
tf 5000 and tf 0 -> IncorrectProgramId (0 ghosts); vq5
mint-base5 at tf 5000 and tf 0 -> custom 3 (4 ghosts); vq1
mint-base at tf 5000 -> custom 3 (0 ghosts).

## Limits

- Receipts are LiteSVM executions against the original, control,
  and candidate program images; they pin observed behaviour, not
  source intent. Error-site lines are recorded per image in each
  report row's `error_sites` field (original/rebuild line numbers
  differ); they are never compared across images.
- Ghost counts are reported as measured. The event-placement
  mechanism above is consistent with every measured cell but was
  not separately instrumented.
- Sell-side base-vault transfer faults (mint/amount/state on
  vb2..vb5 in the sell direction) were not measured as
  standalone cases; the sell-side ghost table above covers
  quote-vault faults and owner-program faults only.
- No claim is made about program behaviour outside the measured
  cases, and no source change is proposed here.

Made via @slopdotcash
