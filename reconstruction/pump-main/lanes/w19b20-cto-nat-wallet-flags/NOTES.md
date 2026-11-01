# w19b20-cto-nat-wallet-flags

Target `0x22a10` `admin_cto::execute`, 27,400 B. PR #4196: 0.97424, 157 slots, zero losses, every region except C1 byte-exact. #4202 (w19a03) unions this gene and reaches 1.0. The orchestrator stopped this lane's land.py run for #4202's priority gate, so #4196 did not merge.

Source shape, each measured on the slim oracle and then a real build:

- Sweep arms use early returns only. All returns share one lifetime join (0x3c50/0x3c58) and only the final `Ok(amount)` takes the normal path, so its tag test threads past 0x3c60 to 0x3c68. On main 18d76df this alone moved W2 from 424 to 454 and made the join's predecessors equal the original's. w19a04 (#4180) found the same form independently and landed first.
- Holder arm holds the 296 check: `if hr&&!holder{289} let (..)=if holder{ if !hr&&!enabled{296} ..`. Fixes the polarity at 0x640 and the 326 name forward together.

Mechanisms worth reusing:

- Branch polarity: SelectionDAGBuilder inverts a branch when its true target is the next IR block. rustc creates blocks in first-reference order, value-0 target first, and RPO visits the value-0 subtree first. So an error block is adjacent to its test only in the `&&` shape, where the continuation is created earlier but must follow the test in RPO. Moving IR blocks in the post-opt module (after `opt -passes=instnamer`, so the text parses) tests a polarity in about a second.
- Inliner: a call site is cold below 2% of the caller's entry frequency, and its threshold drops from 325 to 45. `to_string` costs 130, so frequency alone decides. If it stays out of line at validate's inliner, MemCpyOpt can forward `name` (it needs the call and the memcpy in one block), and execute may still inline `to_string` later. `-print-bfi -print-bfi-func-name=<fn>` on `opt -O3` and `-pass-remarks=inline` show both phases.
- InstCombine turns `icmp ne` into `.not` with swapped successors when every user can be inverted, which is why all holder tests share `%extract.t.not`.
- Tail merge cannot merge blocks ending in a conditional branch here, because BPF `analyzeBranch` fails on them.

Dead end: `if skip{0}else{sweep()?}` (M 2288, layout collapse). The `require!` spellings are byte-identical to `if !c`.
