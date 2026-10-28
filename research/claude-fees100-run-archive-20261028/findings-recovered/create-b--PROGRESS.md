# recovered from the transcript of lane create-b (PROGRESS.md); entries in order

# create-b PROGRESS (lane: re-derive 163920 create_donation_fee_pda::create from the original)

Base: R/shared/frontier/w582 (copied to lanes/create-b/src, pristine). Variants in lanes/create-b/v/<name>/{src,target}.
Tools: lanes/create-b/tools/run.sh NAME (build+score), tools/score.py SYMBOLS.so (ratio for 163920, finds create fn).
Analysis: lanes/create-b/an/orig-163920.txt (original listing with names), cand-w582-create.txt.

## Key facts derived from the original (see findings/create-b.md)
- Original inlines emit! + emit_cpi! fully (Event::data x2, AccountInfo clone, collect loop of 208 bytes,
  AccountMeta vec alloc 34, Instruction::new_with_bytes, invoke_signed). Candidate w582 calls data()/clone/from_iter/exchange_malloc.
- (creator, quote) passes through a Result<(Pubkey,Pubkey)> (tagged, 72 B): 41-byte memcpy temp = Result bytes 24..65.
- Error lines: pool 148/152/156/174, sharing 192/197/204/213/214, payer 221 (all already right in w582).

## Status
(started 2026-10-27 ~11:50)

- 12:50 best = v/v04_c3m (ratio 0.7574, 13824 B/1644 insns, no event data fn). Spec: specs/c3m.py (built on v04_c3 <- v04_wrapperparams).
  Next: pool deser OK/Err placement (orig: JCC+JMP, ok path far at 4784), hoisted load order/regs, sharing merge, emit region.

- 12:56 DONE: 163920 normalized match natively = harvest/create-b-g01 (w583 + create_donation_fee_pda.rs only).
  Source = lanes/create-b/farm2/f1/src (overlay ov/f1). Base for further work: lanes/create-b/base583c (= w583 + create-c-n01),
  mutators in lanes/create-b/mut/*.py (common.py has d1/e3 helpers), overlays via tools/mkov.py, builds via shared/tools/farm.py.
  Remaining for the lane: wait for coordinator Linux confirmation; optionally help Crank 147944.