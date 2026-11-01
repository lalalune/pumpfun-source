# w19b05-shim-w2-colour: authority_bump spill weight (admin_cto 0x22a10)

Target `0x22a10` `admin_cto::execute`, region EV (original 0x50e8-0x5340), pinned at 27,400 B.

Greedy gave r6 to the event `authority_info` pointer and spilled the `authority_bump` byte; the original does the reverse. The byte's weight is 1.52e-6
and the pointer's 2.42e-6. Two volatile stores of the byte raise it to 2.98e-6, so the byte evicts the pointer. The two stores (+16 B) repay what the reversed
spill saves. `emit_cpi!` is expanded in place to reach the byte.

Full analysis (coalescer order, late-queue prices, tools): branch `swarm/w19b05-shim-w2-colour`.
