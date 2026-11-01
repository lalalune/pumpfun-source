# w19a11-shim-arghint: physreg-copy hint through an extra call argument (admin_cto 0x22a10)

An extra register argument at an existing call, through `ptp` plus a transmuted fn pointer, gives one value a physreg COPY:
- priority bit 30 in greedy (it is dequeued with the hinted group, not with its size class);
- its range extended to the call, plus one use of spill weight.
The callee ignores the register, and the call count stays 154/3.

Measured at the sharing-config CPI: the `owner` pointer of the sharing_config clone in r4, M +9 at exactly 27,400 B, C1 only. The source capture equals the IR cell.
