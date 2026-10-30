# Account length and padding chains at true 5 hops (split x boost x tf)

## Problem

Packet #96 measured account size boundaries, padding behaviour, and
length gates on a 3-hop split x boost x tf chain: a pool floor of 211
bytes, a GlobalConfig floor of 907 bytes, fee-table gates at
8/2097/2512 bytes, a UVA floor of 90 bytes, a GVA floor of 544 bytes,
a Token-2022 input sawtooth at 165/166/167 bytes, an exact-165 SPL
tail output, and a check order of GlobalConfig > UVA > pool >
fee-table. This packet re-measures every one of those boundaries on a
true 5-hop chain (three_amm + g4 + g5, final output U5) under
transfer fee, and asks whether the floors, the gates, the check
order, and the padding effects survive depth — and whether padding
moves 5-hop tails, per leg.

All measurements are receipts from three program images (original,
control, candidate) run on the same fixture. All three images agree
on every step: 0 divergent cases.

## Cases

101 cases, 636 receipts, 64 parts. Anchor: buy 10^9 quote pays tail
U5 5,207,955,235,891 with 5 hop events; sell 10^9 base pays 178,541
(restore sell 178,539).

- A (12): main-pool length on buys — 299/279/245/211/210/100/8/0/
  301/400/1000, each followed by a restored buy.
- B (10): pool length by leg position — pool2 299/100/400, p4
  299/100, p5 299/0 on buys, main 299/0 and p5 0 on sells, each with
  a restored leg.
- C (11): GlobalConfig length — 948/907/906/900/500/100/0/950/2000,
  each with a restored buy; a sweep under a broken config; a boost
  under a broken config.
- D (13): fee-table length — 4096/4097/3000/2512/2511/2097/2096/1/0/
  5000, stable 4073/4072, each with a restored buy; a downstream
  sweep/collect/buy chain under a short table.
- E (10): UVA length — claim at 136/90/200/1000; claim at 89/1/0
  followed by extend and claim; trade at UVA 89/0; close at 89
  followed by init.
- F (7): GVA length — sync+claim at 543/544/600/1000/100/0, plus a
  543-failure restore case.
- G (24): token-account length — userquote (Token-2022 input, 178)
  164/165/166/167/100/0/200; U5 (SPL tail output, 165) 164/166/167/
  200; main quote vault (Token-2022, 178) 164/165/167/180; buyback
  ATA (182) 181/170/165/183/200; quote mint (278) 100/200/277/300,
  each with a restored buy.
- H (9): check order — pool+UVA, config+UVA, fee+UVA, pool+fee,
  pool+config, config+fee (break both, restore one, restore both);
  a downstream sweep chain under a broken pool; a pool walk and a
  fee walk of four sequential buys.
- T (5): transfer-fee variants — pool-211 buys at bps 0 and 5000;
  cfg-906, fee-2511, and mint-277 buys at bps 5000.

## Result

- Pool floor exactly 211 bytes at depth 5: 211..260 price with
  virtual_quote_reserves read as 0 (tail 5,207,950,056,210, anchor
  minus 5,179,681); 261 and above pay the anchor; 210 and below
  fail InvalidAccountData with 0 events. A successful buy rewrites
  a truncated pool to 287 bytes, so the restore buy lands at
  4,918,089,082,874.
- Leg position shows up in the event count: pool2 at 100 bytes
  fails with 1 event, p4 with 3, p5 with 4. Sell mirrors execution
  order: main-pool 0 bytes fails with 4 events, p5 0 bytes with 0.
- GlobalConfig floor exactly 907 bytes (948/950/2000 anchor; 906
  and below InvalidAccountData). A protocol sweep survives a
  broken config (cfg 500 sweep succeeds, 1 event) while a boost
  under cfg 500 fails InvalidAccountData.
- Fee table: 0..7 fail 3001, 8..2096 fail 3003, 2097..2511 fail
  6083, 2512..4096 fall back to flat fees (tail anchor + 1 =
  5,207,955,235,892); exactly 4097 activates the exotic branch
  (anchor tail); 5000 pays the anchor. Stable 4073 falls back to
  flat (+1); stable 4072 fails 6082 (FeeTiersEmpty, fees.rs:160)
  after 2 hop events. Downstream legs under a short table still
  run: sweep, collect, and buy all succeed.
- UVA floor exactly 90 bytes: claim at 89 fails 3003, extend
  restores, claim succeeds; claim at 1/0 fails 3001, extend fails
  6027, claim fails 3001; trade with UVA 89 fails 3003, with 0
  fails 3001; close at 89 fails 3003 and init fails 3003.
- GVA floor exactly 544 bytes for both sync and claim: 543/100
  fail 3003, 0 fails 3001; restore sync is a no-op (0 events),
  restore claim succeeds.
- Token accounts: the Token-2022 input sawtooth from #96 holds at
  depth 5 (164 fail, 165 ok, 166 fail, 167+ ok). The SPL tail
  output requires exactly 165 bytes (164/166/167/200 all
  InvalidAccountData). The main quote vault: 164
  InvalidAccountData, 165/167 custom 13, 180 ok — but its restore
  buy pays 4,956,404,517,853, above the standard restore. The
  buyback ATA: 181/170/165 custom 13, 183/200 ok. The quote mint:
  100 InvalidAccountData, 200/277 fail 6007, 300 ok.
- Check order at depth 5 is GlobalConfig > UVA > pool >
  fee-table, identical to #96.
- Byte restore is not book restore: the pool walk's 3rd/4th buys
  pay 4,651,437,646,524 / 4,406,213,485,300 while the fee walk's
  pay 4,651,756,704,513 / 4,406,498,856,365. A terminal-leg
  rewrite moves the restore buy to 4,918,076,339,760 (vs
  4,918,089,082,874 standard); sweeps before restore move it to
  4,918,089,274,853.
- Transfer-fee variants: pool-211 tf0 buy 5,259,035,241,762
  (full-pool tf0 5,259,040,470,738, minus 5,228,976); pool-211
  tf5000 buy 2,668,073,057,012 (full-pool tf5000 2,668,075,748,732,
  minus 2,691,720). The cfg-906, fee-2511, and mint-277 gates are
  tf-independent (InvalidAccountData / 6083 / 6007 under tf5000).

## Limits

- These boundaries were measured on one fixture route (the
  split x boost x tf 5-hop chain with this pool set, this fee
  table, and these token programs). Other routes, other pool
  states, and other fee-table shapes may price differently; the
  packet pins this route's behaviour, not a general rule.
- Lengths are account data lengths as presented to the program.
  Padding bytes are zeros unless stated; non-zero padding was not
  measured here.
- Failing-buy panic behaviour (#146) is out of scope: no case
  here fails on slippage, so no panic-vs-6004 comparison is made.
- Agreement across the three images is agreement on these 636
  receipts only. It is not a claim about the whole program.

Made via @slopdotcash
