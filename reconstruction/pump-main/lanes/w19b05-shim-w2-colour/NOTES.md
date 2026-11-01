# w19b05-shim-w2-colour: spill-weight shims (admin_cto 0x22a10)

Target `0x22a10` `admin_cto::execute`, regions EV (original 0x50e8-0x5340) and W2 (original 0x5cc0-0x5dc8), pinned at 27,400 B.

1. Event path. Greedy gave r6 to the `authority_info` pointer and spilled the `authority_bump` byte; the original does the reverse. The byte's weight is 1.52e-6
   and the pointer's 2.42e-6. Two volatile stores of the byte raise it to 2.98e-6, so the byte evicts the pointer. The two stores (+16 B) repay what the reversed
   spill saves. `emit_cpi!` is expanded in place to reach the byte.
2. Wallet create block. The buffer pointer (w 6.67e-8) evicted `coin_empty` (w 2.04e-8) from r7, so the accounts piece found r7 busy and took r8. Six volatile stores
   of `coin_empty` raise it to 6.96e-8, so the buffer waits for the second stage and the accounts piece takes r7 as in the original. Seven 312 placeholders repay the 56 B.

Full analysis (coalescer order, late-queue prices, tools): branch `swarm/w19b05-shim-w2-colour`.
