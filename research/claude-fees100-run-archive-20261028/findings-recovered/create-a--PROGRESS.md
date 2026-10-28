# recovered from the transcript of lane create-a (PROGRESS.md); entries in order

# create-a lane PROGRESS (incremental strategy)
Target: orig window 163920 (instructions::fee_sharing::create_donation_fee_pda::create, 13800 B / 1641 insns)
+ eliminate the extra standalone <DonationFeePdaCreated as Event>::data (648 B).
Lane dir: R/lanes/create-a ; src = clone of w582 ; target = warm native target ; outputs in out/ ; scratch in work/.
## Status
- 11:50 lane set up; baseline build running.

# create-a lane PROGRESS (incremental strategy)
Target: orig window 163920 (13800 B / 1641 insns) + eliminate standalone <DonationFeePdaCreated as Event>::data.
Lane dir: R/lanes/create-a ; variant trees src-<name>/target-<name> made by work/gen.py from vars/<spec>.py
(BODY = {line: text} for lines>=111 of create_donation_fee_pda.rs; LIB_HANDLER replaces lib.rs line 243).
Build+measure: work/run.sh <name> [rustc args] -> out/<name>-*, one line in work/results.log (BASE=w582|w583 env).
Analysis: work/blocks.py (block match), work/chains.py (MBP chain layout), work/errsites.py (ToString/Display by line),
work/ct.py (funcs/calls/dis). Inline remarks: add -Cremark=inline (no codegen change).
## Status
- Frontier moved to w583 at 12:10 (only buyback/state/ordered.ld differ; Create files identical). New variants use w583.
- Event::data inlining solved several ways (C, v1); remaining = exact layout/copies. See findings/create-a.md.