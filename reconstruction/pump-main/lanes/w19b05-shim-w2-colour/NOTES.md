# w19b05-shim-w2-colour: spill-weight shims (admin_cto 0x22a10)

Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B.

1. EV (#4155): two volatile `authority_bump` stores let the byte evict the `authority_info` pointer from r6.
2. W2 (original 0x5cc0-0x5dc8): the buffer pointer (w 6.67e-8) evicted `coin_empty` (w 2.04e-8) from r7, so the accounts piece found r7 busy and took r8. Six volatile
   `coin_empty` stores raise it to about 7e-8, so the buffer waits for the second stage and the accounts piece takes r7 as in the original. Seven placeholders (312, sweep gate, 648, 664, Clock::get) repay the 56 B.

Full analysis (coalescer order, late-queue prices, tools): branch `swarm/w19b05-shim-w2-colour`.
