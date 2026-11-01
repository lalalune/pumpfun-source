# w19b17-shim-collapse-pin: C1 Rc trap weight on the natural base

Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B. Base main e59b48eb1 (0.81611, M 2,725). Result: 0.83887, M 2,801, 2,253 slots, 27,400 B.

A 1:4 weight on the `authority` clone's data Rc overflow trap (`aicd::<250000>`, marked shim) moves C1's spill and register choices to the original's; a second `st` byte read repays 8 B. Tools and the layout-cliff decision table: `origin/swarm/w19b17-shim-collapse-pin`.
