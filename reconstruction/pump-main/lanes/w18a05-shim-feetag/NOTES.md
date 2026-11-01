# w18a05-shim-feetag: creator==sharing_config compare kept in memory

Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B. Base 665ffe46b: 0.70889, M 2,367, 3,091 slots.
After: 0.70979, M 2,370, 3,141 slots, 27,400 B, 1034/1034, no losses or raw losses.

The first half of the `shared` test writes the compare with `write_volatile` and reads it back from memory. That construct costs about 40 B at
the head of E1. Removing placeholder reads repays it: the two at line 312, the one at line 664 and the one in the Clock::get error path.
Differing positional slots rise by 50 while aligned tokens rise by 3, so this is not byte-identical progress in that metric.

The fee-tag phi notes and tools are on `origin/swarm/w18a05-shim-feetag`.
