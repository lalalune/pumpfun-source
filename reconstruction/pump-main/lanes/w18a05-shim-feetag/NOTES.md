# w18a05-shim-feetag: creator==sharing_config compare byte kept in its stack temp

Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B. Base 7d8ad9f5b: 0.7038, M 2,350, 3,184 slots.
After: 0.7044, M 2,352, 3,180 slots, 27,400 B, 1034/1034, no losses or raw losses, differential 388 cases and 0 mismatches.

The first half of the `shared` test now reads the compare byte back through `read_volatile` (+56 B at the head of E1).
Seven of the eight line-312 placeholder reads repay it. V1, V5, S2 +1 and W2 +3 against E1 -1 and T1 -3; all3 is 2,921 against 2,922, so this is
register and frame naming from a changed RA start, not structure. The head of E1 still differs from the original.

The fee-tag phi notes and tools are on `origin/swarm/w18a05-shim-feetag`.
