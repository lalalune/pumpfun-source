# coordbodyA lane PROGRESS (base L06: 899 normalized / 165 raw, identity recipe)

Durable root W=/Users/shawwalters/Documents/Codex/2026-10-24/claude-pump-work. Lane src: W/lanes/coordbodyA/src (copy of
W/base/current/pump = L06). Builds: W/lanes/coordbodyA/work/<tag> (tools/try.sh <tag> [src] [workslot]).
Targets: W/targets/r4-coordbodyA.json (25 unmatched windows < 0x80000 with Source sites, body differs).
Line-neutral editing on the layout base: every existing Source site stays on its current line (pad blocks rebalanced).

## Experiments
- b00: unchanged L06 source -> unstripped sha 7bc1563b49... = base, 899/165, no gains/losses, runtime_valid, 28 s. Harness reproduces.
- fr1 (validate_fee_recipient: mayhem branch first, require! forms, lines 19/35): 0.853, no gain.
- fr2 (mayhem first, if/else err! forms, lines 19/35): same layout as base (return block mid-function, ret/tag spill slots swapped), 0.908.
- fr3 (mayhem first, early-return form: `if R {return Ok(())} return err!(..)` at 19, `if N {return Ok(())} err!(..)` at 35): GAIN 0x3dd78 -> 900/165, no losses. Applied to lane src. DELIVERED coordbodyA-01.
- fr4 (match bool), fr5 (require! + return Ok): base layout, no gain.
  Note: original 0x3dd78 site lines are 35 (normal path) and 19 (mayhem path); coords.py prints 35,35 (re-reads the first line slot).
- sp1/sp2 (sell.rs helpers appended at original lines: check_bonding_curve_v2 126/133, buyback_fee_recipient 145; 6 call
  sites in lib.rs 367/692/1040/1045 and buy.rs 17/37 replaced in place): GAIN 0x6eed8 (both require! and let-else forms).
  0x6f3e8 at 0.971: Ok/Err branch emitted as `jne` instead of the original `jeq tag,2,+1; ja`.
- bb1 (if-let Err return), bb2 (match Err first): same as sp1. bb3 (`validate(..).map(|_| account)`): GAIN 0x6f3e8 ->
  902/165, no losses. Applied sp1+bb3 to lane src. DELIVERED coordbodyA-02 (cumulative).
  Note: original sites 0x6eed8 are 133 and 126 (coords.py reports 133,133: shared stack slot).
- bv1..bv4 (trade_v3.rs validate_buyback_fee_recipient_account helper for 0x7e490 at lines 165-190, called from check_quote
  (token path) and the three v3 SOL validations): best bv3 (`let owner={borrow; deserialize; mint check; token.owner}`) 0.826.
  bv5..bv7 (Global::validate_buyback_fee_recipient taking &Pubkey): 0x7e490 size right (0.844) but loses 0x6f3e8 -> rejected.
- ct1 (buy_v2.rs check_token_account for 0x160d0 at 106-123; v2 buy/buy_exact/sell_v2 call sites in place): 0.901, only
  stack offsets differ (slice temp -0x48 vs -0x1e8, frame 0x10 smaller).
- ct2/ct3 (explicit `let mut buf:&[u8]=&data;` / `let mut buf=&data[..];`): GAIN 0x160d0 -> 903/165, no losses (identical
  binaries). Applied ct2. DELIVERED coordbodyA-03 (cumulative).
  Insight: the original deserializes through an explicit slice local (`let mut buf = &data[..]`), not `&mut &data[..]`.
