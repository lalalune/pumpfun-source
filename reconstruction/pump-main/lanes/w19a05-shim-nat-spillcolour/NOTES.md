# w19a05-shim-nat-spillcolour

Target 0x22a10 admin_cto::execute, pinned at 27,400 B. Base main fad4cb028: 0.92962, M 3,104, 1,960 slots.
Result: 0.93142, M 3,110, 1,957 slots, 27,400 B, 1034/1034, no losses.

Mechanism: the sharing-config clone run's 1:20 Rc trap weight moves from the global lamports clone to the authority lamports clone, so the 3-reference spill slots of the run take the original's processing order. Registers are unchanged in the run's tile pointers. Tables and tools: origin/swarm/w19a05-shim-nat-spillcolour.
